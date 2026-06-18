from django.db import models
from django.conf import settings


class Report(models.Model):
    TYPE   = [('harassment','Harassment'),('fraud','Fraud'),('content','Content'),('other','Other')]
    STATUS = [('open','Open'),('reviewing','Under Review'),('resolved','Resolved'),('dismissed','Dismissed')]

    reporter    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_reports')
    accused     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reports')
    type        = models.CharField(max_length=15, choices=TYPE)
    description = models.TextField()
    status      = models.CharField(max_length=15, choices=STATUS, default='open')
    admin_note  = models.TextField(blank=True)
    action_taken = models.CharField(max_length=100, blank=True)
    resolved_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_reports'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report #{self.id} ({self.type}) by {self.reporter}'
