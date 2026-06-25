from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, TutorProfile, LearnerProfile


class TutorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TutorProfile
        fields = '__all__'
        read_only_fields = ('user', 'rating', 'rating_count', 'total_sessions', 'pass_rate', 'balance')


class LearnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LearnerProfile
        fields = '__all__'
        read_only_fields = ('user', 'total_sessions', 'total_assessed', 'pass_count')


class UserSerializer(serializers.ModelSerializer):
    tutor_profile   = TutorProfileSerializer(read_only=True)
    learner_profile = LearnerProfileSerializer(read_only=True)
    full_name       = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'bio', 'phone', 'country',
            'is_suspended', 'created_at',
            'tutor_profile', 'learner_profile',
        ]
        read_only_fields = ('id', 'created_at', 'is_suspended')


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'first_name', 'last_name', 'role', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        email    = validated_data['email']
        validated_data.setdefault('username', email.split('@')[0])
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # auto-create profiles
        role = user.role
        if role in ('learner', 'both'):
            LearnerProfile.objects.create(user=user)
        if role in ('tutor', 'both'):
            TutorProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        from django.contrib.auth.backends import ModelBackend
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            # Check if an inactive account exists with correct password (unverified email)
            try:
                candidate = User.objects.get(email=data['email'])
                if not candidate.is_active and candidate.check_password(data['password']):
                    # Correct credentials but email not verified — signal the frontend
                    data['user'] = candidate
                    data['needs_verification'] = True
                    return data
            except User.DoesNotExist:
                pass
            raise serializers.ValidationError('Invalid credentials.')
        if user.is_suspended:
            raise serializers.ValidationError('This account has been suspended.')
        data['user'] = user
        return data


class PublicTutorSerializer(serializers.ModelSerializer):
    """Lightweight tutor listing for AI match & browsing."""
    full_name     = serializers.ReadOnlyField()
    subjects      = serializers.JSONField(source='tutor_profile.subjects')
    specialities  = serializers.JSONField(source='tutor_profile.specialities')
    hourly_rate   = serializers.DecimalField(source='tutor_profile.hourly_rate', max_digits=8, decimal_places=2)
    rating        = serializers.DecimalField(source='tutor_profile.rating', max_digits=3, decimal_places=2)
    rating_count  = serializers.IntegerField(source='tutor_profile.rating_count')
    total_sessions = serializers.IntegerField(source='tutor_profile.total_sessions')
    pass_rate     = serializers.FloatField(source='tutor_profile.pass_rate')
    is_featured   = serializers.BooleanField(source='tutor_profile.is_featured')

    class Meta:
        model  = User
        fields = [
            'id', 'full_name', 'avatar', 'bio', 'country',
            'subjects', 'specialities', 'hourly_rate',
            'rating', 'rating_count', 'total_sessions', 'pass_rate', 'is_featured',
        ]
