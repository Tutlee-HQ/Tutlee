from django.db import models
from django.conf import settings


class Session(models.Model):
    STATUS = [
        ('scheduled',  'Scheduled'),
        ('live',       'Live'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
        ('no_show',    'No-show'),
        ('rescheduled','Rescheduled'),
    ]
    learner       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learner_sessions')
    tutor         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_sessions')
    subject       = models.CharField(max_length=100)
    topic         = models.CharField(max_length=200, blank=True)
    scheduled_at  = models.DateTimeField()
    duration_mins = models.PositiveIntegerField(default=60)
    status        = models.CharField(max_length=15, choices=STATUS, default='scheduled')
    amount        = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    recording_url = models.URLField(blank=True)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'Session {self.id}: {self.learner} → {self.tutor} ({self.subject})'


class SessionRating(models.Model):
    """Post-session survey — learner rates tutor."""
    session       = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='rating')
    rater         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    punctuality   = models.PositiveSmallIntegerField()   # 1-5
    explanation   = models.PositiveSmallIntegerField()   # 1-5
    overall       = models.PositiveSmallIntegerField()   # 1-5
    comment       = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Rating for Session {self.session_id} by {self.rater}'
