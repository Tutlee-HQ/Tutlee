from rest_framework import serializers
from .models import Assessment


class AssessmentSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()
    subject_display = serializers.ReadOnlyField(source='subject')

    class Meta:
        model  = Assessment
        fields = '__all__'
        read_only_fields = ('learner', 'score', 'passed', 'status', 'suggestion', 'created_at', 'completed_at')

    def get_learner_name(self, obj):
        return obj.learner.full_name


class SubmitAssessmentSerializer(serializers.Serializer):
    answers = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
