from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('tutor',   'Tutor'),
        ('both',    'Both'),
        ('admin',   'Admin'),
    ]
    email    = models.EmailField(unique=True)
    role     = models.CharField(max_length=10, choices=ROLE_CHOICES, default='learner')
    avatar   = models.FileField(upload_to='avatars/', blank=True, null=True)
    bio      = models.TextField(blank=True)
    phone    = models.CharField(max_length=20, blank=True)
    country  = models.CharField(max_length=60, blank=True)
    is_suspended = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name()} <{self.email}>'

    @property
    def full_name(self):
        return self.get_full_name() or self.email


class TutorProfile(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tutor_profile')
    subjects      = models.JSONField(default=list)   # e.g. ["Mathematics","Physics"]
    hourly_rate   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    rating        = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count  = models.PositiveIntegerField(default=0)
    total_sessions = models.PositiveIntegerField(default=0)
    pass_rate     = models.FloatField(default=0)      # % of learners who passed assessments
    balance       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_featured   = models.BooleanField(default=False)
    specialities  = models.JSONField(default=list)   # weak areas the tutor is strong in
    is_available  = models.BooleanField(default=True)   # visible to learners
    availability  = models.JSONField(default=dict)      # {weekdays:{start,end}, weekends:{start,end}}

    def __str__(self):
        return f'TutorProfile({self.user.full_name})'


class LearnerProfile(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learner_profile')
    subjects       = models.JSONField(default=list)  # subjects of interest
    weak_areas     = models.JSONField(default=list)  # specific topics they struggle with
    total_sessions = models.PositiveIntegerField(default=0)
    total_assessed = models.PositiveIntegerField(default=0)
    pass_count     = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'LearnerProfile({self.user.full_name})'


class EmailOTP(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code       = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP({self.user.email}, {self.code})'


class SiteContent(models.Model):
    key        = models.CharField(max_length=100, unique=True)
    content    = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'SiteContent({self.key})'


class PasswordResetToken(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token      = models.CharField(max_length=64, unique=True)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PasswordResetToken({self.user.email})'
