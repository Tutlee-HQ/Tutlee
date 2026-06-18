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
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('harassment','Harassment'),('fraud','Fraud'),('content','Content'),('other','Other')], max_length=15)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('open','Open'),('reviewing','Under Review'),('resolved','Resolved'),('dismissed','Dismissed')], default='open', max_length=15)),
                ('admin_note', models.TextField(blank=True)),
                ('action_taken', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('accused', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_reports', to=settings.AUTH_USER_MODEL)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filed_reports', to=settings.AUTH_USER_MODEL)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
