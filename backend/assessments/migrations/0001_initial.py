from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sessions_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=100)),
                ('questions', models.JSONField(default=list)),
                ('answers', models.JSONField(default=list)),
                ('score', models.FloatField(blank=True, null=True)),
                ('passed', models.BooleanField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending','Pending'),('completed','Completed'),('skipped','Skipped')], default='pending', max_length=10)),
                ('suggestion', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessments', to=settings.AUTH_USER_MODEL)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='assessment', to='sessions_app.session')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
