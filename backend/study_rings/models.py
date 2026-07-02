from django.db import models
from django.conf import settings


class StudyRing(models.Model):
    name        = models.CharField(max_length=150)
    subject     = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_rings')
    members     = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='study_rings', blank=True)
    is_featured = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_private  = models.BooleanField(default=False)
    invited_members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='ring_invites', blank=True)
    avatar_color = models.CharField(max_length=7, default='#0D9488')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class RingPost(models.Model):
    ring       = models.ForeignKey(StudyRing, on_delete=models.CASCADE, related_name='posts')
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
