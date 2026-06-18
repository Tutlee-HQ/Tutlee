from django.db import models
from django.conf import settings


class KYTApplication(models.Model):
    STATUS = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]

    tutor             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyt_application')
    id_document       = models.FileField(upload_to='kyt/ids/', blank=True, null=True)
    degree_document   = models.FileField(upload_to='kyt/degrees/', blank=True, null=True)
    demo_video        = models.FileField(upload_to='kyt/demos/', blank=True, null=True)
    interview_done    = models.BooleanField(default=False)
    proficiency_score = models.FloatField(null=True, blank=True)   # 0–100
    status            = models.CharField(max_length=10, choices=STATUS, default='pending')
    rejection_reason  = models.TextField(blank=True)
    admin_notes       = models.TextField(blank=True)
    submitted_at      = models.DateTimeField(auto_now_add=True)
    reviewed_at       = models.DateTimeField(null=True, blank=True)
    reviewed_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='kyt_reviews'
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'KYT({self.tutor.full_name}) — {self.status}'

    @property
    def steps(self):
        return {
            'id':        bool(self.id_document),
            'degree':    bool(self.degree_document),
            'demo':      bool(self.demo_video),
            'interview': self.interview_done,
        }
