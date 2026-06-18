from django.db import models
from django.conf import settings


class Transaction(models.Model):
    TYPE   = [('session_payment','Session Payment'),('payout','Payout'),('platform_fee','Platform Fee'),('penalty','Penalty')]
    STATUS = [('pending','Pending'),('settled','Settled'),('failed','Failed'),('refunded','Refunded')]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    type       = models.CharField(max_length=20, choices=TYPE)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    reference  = models.CharField(max_length=100, unique=True)
    status     = models.CharField(max_length=10, choices=STATUS, default='pending')
    session    = models.ForeignKey('sessions_app.Session', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'TXN-{self.id} ({self.type}) {self.amount}'


class PayoutRequest(models.Model):
    STATUS = [('pending','Pending'),('approved','Approved'),('declined','Declined'),('paid','Paid')]

    tutor          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payout_requests')
    sessions_count = models.PositiveIntegerField(default=0)
    gross          = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee   = models.DecimalField(max_digits=10, decimal_places=2)
    net            = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=10, choices=STATUS, default='pending')
    reviewed_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_payouts'
    )
    created_at     = models.DateTimeField(auto_now_add=True)
    reviewed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Payout #{self.id} for {self.tutor} — {self.status}'
