from rest_framework import serializers
from .models import KYTApplication


class KYTApplicationSerializer(serializers.ModelSerializer):
    tutor_name  = serializers.SerializerMethodField()
    tutor_email = serializers.SerializerMethodField()
    steps       = serializers.ReadOnlyField()

    class Meta:
        model  = KYTApplication
        fields = '__all__'
        read_only_fields = ('tutor','status','submitted_at','reviewed_at','reviewed_by')

    def get_tutor_name(self, obj):
        return obj.tutor.full_name

    def get_tutor_email(self, obj):
        return obj.tutor.email
