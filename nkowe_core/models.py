"""
Nkowe Core: the new, additive domain layer described in the forensic audit
(§10-16, "Hybrid Migration" — see
Nkowe_Legacy_Codebase_Forensic_Audit_and_Migration_Strategy.md §14).

Nothing in this app modifies or replaces `account`, `classroom_app`,
`exam_app`, or `library_app` — this is the strangler-fig pattern: a new
core that existing apps grow to point at over time, starting with new
writes only (see nkowe_core/signals.py) while the legacy tables keep
working unchanged.

Four models, in the order data flows through them:

    LearnerIdentity  — one per human learner, independent of login
    LearningJourney  — a named, ongoing thread of engagement (one institution
                        or program over time)
    Enrollment       — a learner's time-bounded membership within one journey
    LearnerRecordEvent — a provenance-tagged fact/observation/inference/
                        recommendation about a learner, fed by existing apps

Two open product decisions are called out inline below with
[DECISION REQUIRED] — the schema is deliberately built so neither decision
is foreclosed by today's implementation.
"""
import uuid

from django.conf import settings
from django.db import models


class LearnerIdentity(models.Model):
    """
    A persistent identity for a human learner, independent of login
    credentials (audit §10.1).

    `user` is nullable on purpose: the target state described in the new
    Nkowe vision includes a learner who is known to the system (enrolled by
    an institution, has a longitudinal record) before they've claimed or
    activated their own login. Today every LearnerIdentity is created 1:1
    with a CustomUser at account-creation time (see signals.py,
    mirroring the existing Token/ChatRoom auto-provisioning pattern in
    account/signals.py) — the nullable FK just means that assumption isn't
    baked into the schema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='learner_identity',
    )
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user_id:
            return self.user.get_username()
        return self.display_name or str(self.id)


class LearningJourney(models.Model):
    """
    A named, ongoing thread of a learner's engagement with one institution
    or program over time (audit §10.2). Every Enrollment belongs to
    exactly one journey.

    [DECISION REQUIRED — audit §10.2] journey *boundaries* are a real
    product decision Electroll hasn't made yet: is "attends Institution X"
    always exactly one journey, or could a learner have separate journeys
    per program/cohort within the same institution (e.g. "coding academy"
    as one journey vs. several)? Nothing here forces an answer — a learner
    can have any number of LearningJourney rows, institutional or
    self-directed, and this app makes no assumption about how many
    journeys one institution relationship produces. The MVP default (see
    the Enrollment backfill migration, added once this app's initial
    migration exists) will be the conservative one: one journey per
    (learner, institution) pair.

    `institution` is nullable specifically so a self-directed, non-
    institutional journey type can exist (audit §15 MVP item 3 — proving
    multi-journey support means a learner needs a *second*, genuinely
    different kind of journey, not just the schema's theoretical capacity
    for one).
    """
    JOURNEY_TYPE_INSTITUTIONAL = 'institutional'
    JOURNEY_TYPE_SELF_DIRECTED = 'self_directed'
    JOURNEY_TYPE_CHOICES = [
        (JOURNEY_TYPE_INSTITUTIONAL, 'Institutional'),
        (JOURNEY_TYPE_SELF_DIRECTED, 'Self-Directed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(LearnerIdentity, on_delete=models.CASCADE, related_name='journeys')
    journey_type = models.CharField(max_length=20, choices=JOURNEY_TYPE_CHOICES, default=JOURNEY_TYPE_INSTITUTIONAL)
    institution = models.ForeignKey(
        'classroom_app.Institution',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='learning_journeys',
    )
    title = models.CharField(
        max_length=255,
        help_text="Human-readable label, e.g. 'Greenfield Secondary School' or 'Self-Directed: Python Fundamentals'.",
    )
    started_at = models.DateField()
    ended_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.learner} — {self.title}"


class Enrollment(models.Model):
    """
    A learner's time-bounded membership within one LearningJourney (audit
    §10.1). Replaces the bare `Student.institutions` M2M as the load-
    bearing membership record going forward — the legacy field is left in
    place and untouched (nothing reads it from here) until a backfill
    migration and a deliberate cutover retire it (audit §12, §13).
    """
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    PROVENANCE_VERIFIED = 'verified_institutional'
    PROVENANCE_LEGACY_IMPORT = 'legacy_import'
    PROVENANCE_SELF_REPORTED = 'self_reported'
    PROVENANCE_CHOICES = [
        (PROVENANCE_VERIFIED, 'Verified institutional data'),
        (PROVENANCE_LEGACY_IMPORT, 'Legacy import (date approximate)'),
        (PROVENANCE_SELF_REPORTED, 'Self-reported'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(LearningJourney, on_delete=models.CASCADE, related_name='enrollments')
    institution = models.ForeignKey(
        'classroom_app.Institution',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='enrollments',
    )
    # Free-text until a formal Program/Cohort model exists (out of scope for
    # this first slice — see audit §12 duplicate-Question-model note for the
    # same "don't build the formal model before the decision is made" logic).
    program = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    # No real enrollment date exists anywhere in the legacy data (the M2M
    # table being backfilled from has none) — provenance tagging exists so
    # the new record is honest about that rather than fabricating false
    # precision (audit §13).
    provenance = models.CharField(max_length=30, choices=PROVENANCE_CHOICES, default=PROVENANCE_VERIFIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.journey.learner} @ {self.institution or self.program} ({self.status})"


class LearnerRecordEvent(models.Model):
    """
    A single provenance-tagged fact/observation/inference/recommendation
    about a learner (audit §10.3 — "the single highest-leverage piece of
    new infrastructure in the whole migration"). Existing apps *emit* into
    this table on meaningful events (see signals.py: ExamAttempt and
    StudentAssignment completion) rather than being rewritten internally —
    this table is purely additive, nothing in exam_app/classroom_app reads
    from it (yet), so there is no behavior-change risk from adding it.
    """
    CATEGORY_FACT = 'fact'
    CATEGORY_OBSERVATION = 'observation'
    CATEGORY_INFERENCE = 'inference'
    CATEGORY_RECOMMENDATION = 'recommendation'
    CATEGORY_CHOICES = [
        (CATEGORY_FACT, 'Fact'),
        (CATEGORY_OBSERVATION, 'Observation'),
        (CATEGORY_INFERENCE, 'Inference'),
        (CATEGORY_RECOMMENDATION, 'Recommendation'),
    ]

    SOURCE_APP_CHOICES = [
        ('exam_app', 'Exam App'),
        ('classroom_app', 'Classroom App'),
        ('library_app', 'Library App'),
        ('nkowe_core', 'Nkowe Core'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(LearnerIdentity, on_delete=models.CASCADE, related_name='record_events')
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.SET_NULL, null=True, blank=True, related_name='record_events',
    )
    source_app = models.CharField(max_length=50, choices=SOURCE_APP_CHOICES)
    event_type = models.CharField(max_length=100, help_text="e.g. 'exam_attempt_completed', 'assignment_completed'.")
    provenance_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_FACT)
    responsible_actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Who/what produced this event — the learner themself, a teacher, or null for system-generated.",
    )
    payload = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(help_text="When the underlying thing happened, not when this row was written.")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['learner', '-occurred_at']),
        ]

    def __str__(self):
        return f"{self.learner} — {self.event_type} ({self.occurred_at:%Y-%m-%d})"
