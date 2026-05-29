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
            name='KYTApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_document', models.FileField(blank=True, null=True, upload_to='kyt/ids/')),
                ('degree_document', models.FileField(blank=True, null=True, upload_to='kyt/degrees/')),
                ('demo_video', models.FileField(blank=True, null=True, upload_to='kyt/demos/')),
                ('interview_done', models.BooleanField(default=False)),
                ('proficiency_score', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')], default='pending', max_length=10)),
                ('rejection_reason', models.TextField(blank=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('tutor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='kyt_application', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kyt_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-submitted_at']},
        ),
    ]
