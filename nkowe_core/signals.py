"""
Signal receivers that make nkowe_core additive rather than a migration
Electroll has to run by hand everywhere: new CustomUsers get a
LearnerIdentity automatically (mirrors the Token/ChatRoom pattern in
account/signals.py), and two existing completion events start feeding the
new longitudinal record without exam_app/classroom_app being touched
internally (audit §10.3, §16 Weeks 5-8).
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from account.models import CustomUser
from classroom_app.assignment.models import StudentAssignment
from exam_app.models import ExamAttempt

from .models import LearnerIdentity, LearnerRecordEvent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def create_learner_identity(sender, instance=None, created=False, **kwargs):
    if created and instance:
        LearnerIdentity.objects.get_or_create(
            user=instance,
            defaults={'display_name': instance.get_username()},
        )


def _learner_identity_for(user):
    if user is None:
        return None
    return LearnerIdentity.objects.filter(user=user).first()


# --- ExamAttempt completion -> LearnerRecordEvent -----------------------
#
# post_save alone can't tell whether is_completed just turned True or was
# already True on a previous save, so pre_save stashes the value on disk
# before the write lands; post_save compares against it. This guarantees
# exactly one event per completion, not one per subsequent save.

@receiver(pre_save, sender=ExamAttempt)
def _stash_previous_exam_attempt_completion(sender, instance, **kwargs):
    if instance.pk:
        instance._was_completed = (
            ExamAttempt.objects.filter(pk=instance.pk)
            .values_list('is_completed', flat=True)
            .first()
        )
    else:
        instance._was_completed = False


@receiver(post_save, sender=ExamAttempt)
def emit_exam_attempt_event(sender, instance, created, **kwargs):
    was_completed = getattr(instance, '_was_completed', False)
    if not instance.is_completed or was_completed:
        return

    learner = _learner_identity_for(instance.student)
    if learner is None:
        logger.warning(
            "ExamAttempt %s completed but user %s has no LearnerIdentity yet; skipping LearnerRecordEvent.",
            instance.pk, instance.student_id,
        )
        return

    LearnerRecordEvent.objects.create(
        learner=learner,
        source_app='exam_app',
        event_type='exam_attempt_completed',
        provenance_category=LearnerRecordEvent.CATEGORY_FACT,
        responsible_actor=instance.student,
        payload={
            'exam_attempt_id': str(instance.custom_id),
            'exam_id': instance.exam_id,
            'exam_title': instance.exam.title,
            'score': instance.score,
        },
        occurred_at=instance.end_time or instance.start_time or timezone.now(),
    )


# --- StudentAssignment completion -> LearnerRecordEvent ------------------
#
# Same stash/compare pattern as above. Note the naming collision in the
# legacy schema: StudentAssignment.student is a FK to ClassroomStudent
# (classroom_app), and ClassroomStudent.student is a FK to Student
# (account app), whose own `.user` is the CustomUser — hence
# `instance.student.student.user` below.

@receiver(pre_save, sender=StudentAssignment)
def _stash_previous_student_assignment_status(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_status = (
            StudentAssignment.objects.filter(pk=instance.pk)
            .values_list('status', flat=True)
            .first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=StudentAssignment)
def emit_student_assignment_event(sender, instance, created, **kwargs):
    previous_status = getattr(instance, '_previous_status', None)
    if instance.status != 'completed' or previous_status == 'completed':
        return

    classroom_student = instance.student
    user = classroom_student.student.user if classroom_student and classroom_student.student else None
    learner = _learner_identity_for(user)
    if learner is None:
        logger.warning(
            "StudentAssignment %s completed but no LearnerIdentity found for its student; skipping LearnerRecordEvent.",
            instance.pk,
        )
        return

    LearnerRecordEvent.objects.create(
        learner=learner,
        source_app='classroom_app',
        event_type='assignment_completed',
        provenance_category=LearnerRecordEvent.CATEGORY_FACT,
        responsible_actor=user,
        payload={
            'assignment_id': instance.assignment_id,
            'assignment_title': instance.assignment.title,
        },
        occurred_at=instance.submitted_at or timezone.now(),
    )
