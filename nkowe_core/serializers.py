"""
Read/write shapes for the Learner/Guardian/Teacher dashboard endpoints in
views.py. Each learner's data is assembled once through
LearnerDashboardSerializer regardless of who's looking at it (self, a
guardian, a teacher) — access control (who is allowed to see which
learner) lives entirely in views.py, not here.
"""
from rest_framework import serializers

from .models import Enrollment, LearnerIdentity, LearnerRecordEvent, LearningJourney


class LearnerRecordEventSerializer(serializers.ModelSerializer):
    responsible_actor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LearnerRecordEvent
        fields = [
            'id', 'source_app', 'event_type', 'provenance_category',
            'payload', 'occurred_at', 'recorded_at', 'responsible_actor', 'enrollment',
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True, default=None)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'institution', 'institution_name', 'program', 'start_date',
            'end_date', 'status', 'provenance',
        ]


class LearningJourneySerializer(serializers.ModelSerializer):
    enrollments = EnrollmentSerializer(many=True, read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True, default=None)

    class Meta:
        model = LearningJourney
        fields = [
            'id', 'journey_type', 'institution', 'institution_name', 'title',
            'started_at', 'ended_at', 'is_active', 'enrollments',
        ]


class LearnerDashboardSerializer(serializers.ModelSerializer):
    """
    The full self-view / guardian-view / teacher-view payload for one
    learner: their identity, every journey (with nested enrollments), and
    their most recent record events. Whoever is allowed to see this
    learner (LearnerDashboardView for the learner themself,
    GuardianDashboardView for a linked parent, TeacherClassLearnerRecordsView
    for a teacher of a shared classroom) gets the same shape — only the
    view layer decides which learner(s) a given caller may request.
    """
    journeys = LearningJourneySerializer(many=True, read_only=True)
    recent_events = serializers.SerializerMethodField()
    # The CustomUser PK, not LearnerIdentity's own `id` (a separate UUID) —
    # this is what TeacherClassLearnerRecordsView.post expects as
    # `student_user_id`, so the frontend roster view has something usable
    # to submit an observation against without a second lookup.
    user_id = serializers.IntegerField(source='user.id', read_only=True, default=None)
    username = serializers.CharField(source='user.username', read_only=True, default=None)
    first_name = serializers.CharField(source='user.first_name', read_only=True, default=None)
    last_name = serializers.CharField(source='user.last_name', read_only=True, default=None)

    class Meta:
        model = LearnerIdentity
        fields = [
            'id', 'user_id', 'display_name', 'username', 'first_name', 'last_name',
            'journeys', 'recent_events',
        ]

    def get_recent_events(self, obj):
        # Capped rather than paginated: this is a dashboard summary, not a
        # full LLR browse view. Revisit with real pagination once the
        # Learner Growth Timeline (PRD FR-8, [P2]) needs full history.
        events = obj.record_events.all()[:20]
        return LearnerRecordEventSerializer(events, many=True).data
