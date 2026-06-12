from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_emailotp_sitecontent'),
    ]
    operations = [
        migrations.AddField(
            model_name='tutorprofile',
            name='is_available',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tutorprofile',
            name='availability',
            field=models.JSONField(default=dict),
        ),
    ]
