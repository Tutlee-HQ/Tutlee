from rest_framework import serializers
from .models import Transaction, PayoutRequest


class TransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model  = Transaction
        fields = '__all__'
        read_only_fields = ('user', 'reference', 'created_at')

    def get_user_name(self, obj):
        return obj.user.full_name


class PayoutRequestSerializer(serializers.ModelSerializer):
    tutor_name = serializers.SerializerMethodField()

    class Meta:
        model  = PayoutRequest
        fields = '__all__'
        read_only_fields = ('tutor', 'gross', 'platform_fee', 'net', 'sessions_count',
                            'status', 'reviewed_by', 'created_at', 'reviewed_at')

    def get_tutor_name(self, obj):
        return obj.tutor.full_name
