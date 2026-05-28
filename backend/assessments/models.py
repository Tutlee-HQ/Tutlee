from django.db import models
from django.conf import settings


class Assessment(models.Model):
    STATUS = [('pending','Pending'),('completed','Completed'),('skipped','Skipped')]

    session   = models.OneToOneField('sessions_app.Session', on_delete=models.CASCADE, related_name='assessment')
    learner   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessments')
    subject   = models.CharField(max_length=100)
    questions = models.JSONField(default=list)   # list of {text, options:[str], answer:int(index)}
    answers   = models.JSONField(default=list)   # learner's submitted answer indices
    score     = models.FloatField(null=True, blank=True)   # percentage 0-100
    passed    = models.BooleanField(null=True, blank=True)
    status    = models.CharField(max_length=10, choices=STATUS, default='pending')
    suggestion = models.TextField(blank=True)   # rebook / well done etc.
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Assessment {self.id} ({self.subject}) — {self.learner}'

    def calculate_score(self):
        """Grade submitted answers and update score/passed."""
        from django.conf import settings
        from django.utils import timezone
        correct = 0
        for i, q in enumerate(self.questions):
            if i < len(self.answers) and self.answers[i] == q.get('answer'):
                correct += 1
        total = len(self.questions) or 1
        self.score  = round((correct / total) * 100, 1)
        threshold   = getattr(settings, 'ASSESSMENT_PASS_THRESHOLD', 60)
        self.passed = self.score >= threshold
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.suggestion = (
            'Great work! You have a strong understanding. Book your next session to go deeper.'
            if self.passed else
            'Keep it up! Consider rebooking with your tutor to revisit the areas you found tricky.'
        )
        self.save()
        # Update learner profile stats
        try:
            lp = self.learner.learner_profile
            lp.total_assessed += 1
            if self.passed:
                lp.pass_count += 1
            lp.save()
        except Exception:
            pass
        # Update tutor pass_rate
        try:
            from sessions_app.models import Session
            tp        = self.session.tutor.tutor_profile
            all_a     = Assessment.objects.filter(session__tutor=self.session.tutor, status='completed')
            if all_a.exists():
                tp.pass_rate = round(all_a.filter(passed=True).count() / all_a.count() * 100, 1)
                tp.save()
        except Exception:
            pass
        return self.score
