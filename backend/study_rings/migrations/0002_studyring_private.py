from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('study_rings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='studyring',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studyring',
            name='invited_members',
            field=models.ManyToManyField(
                blank=True,
                related_name='ring_invites',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
