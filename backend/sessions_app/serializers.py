from rest_framework import serializers
from .models import Session, SessionRating, Message
from accounts.serializers import UserSerializer


class SessionRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SessionRating
        fields = '__all__'
        read_only_fields = ('rater', 'created_at')


class SessionSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()
    tutor_name   = serializers.SerializerMethodField()
    rating       = SessionRatingSerializer(read_only=True)

    class Meta:
        model  = Session
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_learner_name(self, obj):
        return obj.learner.full_name

    def get_tutor_name(self, obj):
        return obj.tutor.full_name


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model  = Message
        fields = ['id', 'session', 'sender', 'sender_name', 'content', 'created_at']
        read_only_fields = ('sender', 'created_at', 'session')

    def get_sender_name(self, obj):
        return obj.sender.full_name


class BookSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Session
        fields = ['tutor', 'subject', 'topic', 'scheduled_at', 'duration_mins', 'notes']

    def create(self, validated_data):
        learner = self.context['request'].user
        validated_data['learner'] = learner
        # Calculate amount from tutor's hourly rate
        tutor = validated_data['tutor']
        try:
            rate   = float(tutor.tutor_profile.hourly_rate)
            duration_h = validated_data.get('duration_mins', 60) / 60
            validated_data['amount'] = round(rate * duration_h, 2)
        except Exception:
            validated_data['amount'] = 0
        session = Session.objects.create(**validated_data)
        return session
