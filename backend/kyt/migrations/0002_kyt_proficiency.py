from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='kytapplication',
            name='proficiency_questions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='kytapplication',
            name='proficiency_answers',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='kytapplication',
            name='demo_session_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='kytapplication',
            name='demo_session_done',
            field=models.BooleanField(default=False),
        ),
        # Make demo_video nullable (we're removing it from the form but keeping DB col for old data)
        migrations.AlterField(
            model_name='kytapplication',
            name='demo_video',
            field=models.FileField(blank=True, null=True, upload_to='kyt/demos/'),
        ),
    ]
