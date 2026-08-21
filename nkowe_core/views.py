"""
Learner/Guardian/Teacher dashboard endpoints (PRD FR-45/46/47), the first
frontend-facing use of the nkowe_core domain model built in Phase 2 (see
Nkowe_Core_Domain_Model_Phase2_Log.md).

Scope, deliberately: this ships the "Journeys + LLR summary" portion of
FR-45/46 only. Guardian *consent management* and an *access log* are also
named in the PRD for the guardian dashboard, but neither has a backing
model yet (no ConsentGrant or AuditLogEntry model exists anywhere in this
codebase) — building either here would mean faking data or silently
scope-creeping into a new model with no product decision behind it, the
same discipline the audit already applied to LearningJourney boundaries
and Program/Cohort modeling. Both are flagged as follow-up work, not
built.
"""
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Parent, Student
from classroom_app.classroom.models import ClassroomStudent, ClassroomTutor

from .models import LearnerIdentity, LearnerRecordEvent
from .serializers import LearnerDashboardSerializer, LearnerRecordEventSerializer


class LearnerDashboardView(APIView):
    """
    A learner's own self-view of their Longitudinal Learner Record (PRD
    FR-47). Every CustomUser gets a LearnerIdentity automatically at
    account-creation time (nkowe_core/signals.py) and, for accounts that
    predate nkowe_core, via the 0002 backfill migration — so this works for
    any authenticated user, not only accounts with a Student profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            identity = request.user.learner_identity
        except LearnerIdentity.DoesNotExist:
            return Response(
                {"detail": "No learner record exists for this account yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(LearnerDashboardSerializer(identity).data)


class GuardianDashboardView(APIView):
    """
    A guardian's view of their linked children's Longitudinal Learner
    Records (PRD FR-45, Journeys + LLR summary portion only — see module
    docstring for what's deliberately not built here yet).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            parent = request.user.parent
        except Parent.DoesNotExist:
            return Response(
                {"detail": "This account has no guardian (Parent) profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        children = Student.objects.filter(parent=parent).select_related('user')
        results = []
        for student in children:
            try:
                identity = student.user.learner_identity
            except LearnerIdentity.DoesNotExist:
                continue
            results.append(LearnerDashboardSerializer(identity).data)
        return Response(results)


class TeacherClassLearnerRecordsView(APIView):
    """
    Teacher dashboard (PRD FR-46): class-scoped LLR view plus observation
    entry. GET returns each enrolled student's learner record for a
    classroom the requester actually teaches; POST files a new
    `LearnerRecordEvent` (provenance_category=observation) against one of
    those students — the "teacher-observation entity + provenance tagging"
    requirement (Master Document catalogue item 76). Both reject a
    classroom the requester isn't assigned to as a tutor, mirroring the
    membership check scoped_by_classroom_membership() already applies to
    rosters/exams/attachments in classroom_app/classroom/views.py.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _assert_teaches(self, user, classroom_id):
        is_tutor = ClassroomTutor.objects.filter(
            classroom_id=classroom_id, tutor__user=user
        ).exists()
        if not (is_tutor or user.is_staff or user.is_superuser):
            raise PermissionDenied("You are not assigned to this classroom.")

    def get(self, request, classroom_id):
        self._assert_teaches(request.user, classroom_id)
        memberships = ClassroomStudent.objects.filter(
            classroom_id=classroom_id
        ).select_related('student__user')
        results = []
        for membership in memberships:
            try:
                identity = membership.student.user.learner_identity
            except LearnerIdentity.DoesNotExist:
                continue
            results.append(LearnerDashboardSerializer(identity).data)
        return Response(results)

    def post(self, request, classroom_id):
        self._assert_teaches(request.user, classroom_id)
        student_user_id = request.data.get('student_user_id')
        note = (request.data.get('note') or '').strip()
        if not student_user_id or not note:
            return Response(
                {"detail": "student_user_id and note are both required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_member = ClassroomStudent.objects.filter(
            classroom_id=classroom_id, student__user_id=student_user_id
        ).exists()
        if not is_member:
            return Response(
                {"detail": "That student is not enrolled in this classroom."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            identity = LearnerIdentity.objects.get(user_id=student_user_id)
        except LearnerIdentity.DoesNotExist:
            return Response(
                {"detail": "That student has no learner record yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        event = LearnerRecordEvent.objects.create(
            learner=identity,
            source_app='nkowe_core',
            event_type='teacher_observation',
            provenance_category=LearnerRecordEvent.CATEGORY_OBSERVATION,
            responsible_actor=request.user,
            payload={'note': note},
            occurred_at=timezone.now(),
        )
        return Response(LearnerRecordEventSerializer(event).data, status=status.HTTP_201_CREATED)
