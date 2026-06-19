from rest_framework import serializers
from .models import StudyRing, RingPost


class RingPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model  = RingPost
        fields = '__all__'
        read_only_fields = ('author', 'created_at')

    def get_author_name(self, obj):
        return obj.author.full_name


class StudyRingSerializer(serializers.ModelSerializer):
    member_count  = serializers.ReadOnlyField()
    creator_name  = serializers.SerializerMethodField()
    host_name     = serializers.SerializerMethodField()   # alias used by frontend
    is_member     = serializers.SerializerMethodField()
    is_live       = serializers.SerializerMethodField()   # frontend checks this

    class Meta:
        model  = StudyRing
        fields = '__all__'
        read_only_fields = ('creator', 'created_at')

    def get_creator_name(self, obj):
        try: return obj.creator.full_name or f'{obj.creator.first_name} {obj.creator.last_name}'.strip()
        except Exception: return 'Unknown'

    def get_host_name(self, obj):
        return self.get_creator_name(obj)

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(pk=request.user.pk).exists()
        return False

    def get_is_live(self, obj):
        return obj.is_active
