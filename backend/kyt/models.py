from django.db import models
from django.conf import settings


class KYTApplication(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    tutor           = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyt_application')
    id_document     = models.FileField(upload_to='kyt/ids/', blank=True, null=True)
    degree_document = models.FileField(upload_to='kyt/degrees/', blank=True, null=True)

    # Proficiency test - questions set by admin, answers submitted in-system
    proficiency_questions = models.JSONField(default=list, blank=True)
    proficiency_answers   = models.JSONField(default=list, blank=True)
    proficiency_score     = models.FloatField(null=True, blank=True)

    # Demo session - tutor requests a live demo inside Tutlee (no file upload)
    demo_session_requested = models.BooleanField(default=False)
    demo_session_done      = models.BooleanField(default=False)

    interview_done   = models.BooleanField(default=False)
    status           = models.CharField(max_length=10, choices=STATUS, default='pending')
    rejection_reason = models.TextField(blank=True)
    admin_notes      = models.TextField(blank=True)
    submitted_at     = models.DateTimeField(auto_now_add=True)
    reviewed_at      = models.DateTimeField(null=True, blank=True)
    reviewed_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='kyt_reviews'
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return 'KYT({}) - {}'.format(self.tutor.full_name, self.status)

    @property
    def steps(self):
        return {
            'id':          bool(self.id_document),
            'degree':      bool(self.degree_document),
            'proficiency': self.proficiency_score is not None,
            'demo':        self.demo_session_done,
            'interview':   self.interview_done,
        }

    def calculate_proficiency_score(self):
        """Auto-score the proficiency test. Each question must have an answer_key."""
        questions = self.proficiency_questions or []
        answers   = self.proficiency_answers or []
        if not questions:
            return None
        correct = sum(
            1 for i, q in enumerate(questions)
            if i < len(answers) and answers[i] == q.get('answer_key')
        )
        return round(correct / len(questions) * 100, 1)
