from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.SerializerMethodField()
    accused_name  = serializers.SerializerMethodField()

    class Meta:
        model  = Report
        fields = '__all__'
        read_only_fields = ('reporter','status','admin_note','action_taken','resolved_by','created_at','resolved_at')

    def get_reporter_name(self, obj):
        return obj.reporter.full_name

    def get_accused_name(self, obj):
        return obj.accused.full_name
