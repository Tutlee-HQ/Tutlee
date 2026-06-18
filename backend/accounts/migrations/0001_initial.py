from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('username', models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()])),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('learner','Learner'),('tutor','Tutor'),('both','Both'),('admin','Admin')], default='learner', max_length=10)),
                ('avatar', models.FileField(blank=True, null=True, upload_to='avatars/')),
                ('bio', models.TextField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, max_length=60)),
                ('is_suspended', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={'abstract': False},
            managers=[('objects', django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name='TutorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subjects', models.JSONField(default=list)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ('rating_count', models.PositiveIntegerField(default=0)),
                ('total_sessions', models.PositiveIntegerField(default=0)),
                ('pass_rate', models.FloatField(default=0)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_featured', models.BooleanField(default=False)),
                ('specialities', models.JSONField(default=list)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_profile', to='accounts.user')),
            ],
        ),
        migrations.CreateModel(
            name='LearnerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subjects', models.JSONField(default=list)),
                ('weak_areas', models.JSONField(default=list)),
                ('total_sessions', models.PositiveIntegerField(default=0)),
                ('total_assessed', models.PositiveIntegerField(default=0)),
                ('pass_count', models.PositiveIntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='learner_profile', to='accounts.user')),
            ],
        ),
    ]
