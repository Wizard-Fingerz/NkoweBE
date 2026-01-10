from rest_framework import serializers
from .models import DiscussionThread, DiscussionPost, DiscussionThreadReadStatus

class DiscussionPostSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DiscussionPost
        fields = [
            'id',
            'thread',
            'user',
            'user_username',
            'user_full_name',
            'content',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'user_full_name']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() if hasattr(obj.user, "get_full_name") else obj.user.username

class DiscussionThreadSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_full_name = serializers.SerializerMethodField(read_only=True)
    post_count = serializers.IntegerField(read_only=True)
    members_count = serializers.SerializerMethodField(read_only=True)
    is_public = serializers.SerializerMethodField(read_only=True)
    is_private = serializers.SerializerMethodField(read_only=True)
    # Optionally, include posts in thread listing (not recommended for large threads)
    # posts = DiscussionPostSerializer(many=True, read_only=True)

    class Meta:
        model = DiscussionThread
        fields = [
            'id',
            'title',
            'created_by',
            'created_by_username',
            'created_by_full_name',
            'created_at',
            'pinned',
            'visibility',
            'chat_enabled',
            'members',
            'requested_members',
            'post_count',
            'members_count',
            'is_public',
            'is_private',
            # 'posts',
        ]
        read_only_fields = [
            'id', 'created_at', 'created_by_username', 'created_by_full_name',
            'post_count', 'members_count', 'is_public', 'is_private'
        ]

    def get_created_by_full_name(self, obj):
        return obj.created_by.get_full_name() if hasattr(obj.created_by, "get_full_name") else obj.created_by.username

    def get_members_count(self, obj):
        # The creator is considered a member by business logic
        return obj.members.count() + 1

    def get_is_public(self, obj):
        return obj.is_public()

    def get_is_private(self, obj):
        return obj.is_private()

class DiscussionThreadReadStatusSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    thread_title = serializers.CharField(source='thread.title', read_only=True)

    class Meta:
        model = DiscussionThreadReadStatus
        fields = [
            'id',
            'user',
            'user_username',
            'thread',
            'thread_title',
            'last_read_at',
        ]
        read_only_fields = ['id', 'user_username', 'thread_title', 'last_read_at']