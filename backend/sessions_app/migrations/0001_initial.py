from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=100)),
                ('topic', models.CharField(blank=True, max_length=200)),
                ('scheduled_at', models.DateTimeField()),
                ('duration_mins', models.PositiveIntegerField(default=60)),
                ('status', models.CharField(choices=[('scheduled','Scheduled'),('live','Live'),('completed','Completed'),('cancelled','Cancelled'),('no_show','No-show'),('rescheduled','Rescheduled')], default='scheduled', max_length=15)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('recording_url', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learner_sessions', to=settings.AUTH_USER_MODEL)),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-scheduled_at']},
        ),
        migrations.CreateModel(
            name='SessionRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('punctuality', models.PositiveSmallIntegerField()),
                ('explanation', models.PositiveSmallIntegerField()),
                ('overall', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rater', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_ratings', to=settings.AUTH_USER_MODEL)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rating', to='sessions_app.session')),
            ],
        ),
    ]
