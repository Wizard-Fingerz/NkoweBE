from rest_framework import serializers
from .models import SuggestedSolution, SuggestedSolutionVote, SolutionComment

class SolutionCommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = SolutionComment
        fields = [
            "id",
            "user",
            "content",
            "parent",
            "created_at",
            "updated_at",
            "replies",
        ]

    def get_replies(self, obj):
        # Recursively serialize replies (1 level deep for now)
        queryset = obj.replies.all()
        return SolutionCommentSerializer(queryset, many=True).data

class SuggestedSolutionVoteSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    vote_type_display = serializers.CharField(source="get_vote_type_display", read_only=True)
    class Meta:
        model = SuggestedSolutionVote
        fields = [
            "id",
            "user",
            "vote_type",
            "vote_type_display",
            "created_at"
        ]

class SuggestedSolutionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    total_votes = serializers.SerializerMethodField()
    votes = SuggestedSolutionVoteSerializer(many=True, read_only=True)
    comments = SolutionCommentSerializer(many=True, read_only=True)
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = SuggestedSolution
        fields = [
            "id",
            "question",
            "user",
            "content",
            "file",
            "created_at",
            "updated_at",
            "is_active",
            "total_votes",
            "votes",
            "comments",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "total_votes", "votes", "comments"]

    def get_total_votes(self, obj):
        return obj.total_votes()

    def create(self, validated_data):
        # The view must set user as validated_data['user'] before calling create
        return super().create(validated_data)

