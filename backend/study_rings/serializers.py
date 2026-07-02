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
    is_invited    = serializers.SerializerMethodField()
    is_creator    = serializers.SerializerMethodField()
    is_live       = serializers.SerializerMethodField()   # frontend checks this
    members_data  = serializers.SerializerMethodField()   # [{id, full_name, role}]

    class Meta:
        model  = StudyRing
        fields = [
            'id', 'name', 'subject', 'description', 'creator', 'creator_name',
            'host_name', 'is_featured', 'is_active', 'is_live', 'is_private',
            'avatar_color', 'created_at', 'member_count', 'is_member',
            'is_invited', 'is_creator', 'members_data',
        ]
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

    def get_is_invited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.invited_members.filter(pk=request.user.pk).exists()
        return False

    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator_id == request.user.pk
        return False

    def get_is_live(self, obj):
        return obj.is_active

    def get_members_data(self, obj):
        try:
            return [
                {'id': u.id, 'full_name': u.full_name, 'email': u.email, 'role': u.role}
                for u in obj.members.all()
            ]
        except Exception:
            return []
