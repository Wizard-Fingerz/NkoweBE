"""
Backfills a LearnerIdentity for every CustomUser that existed before
nkowe_core was installed. signals.py's post_save receiver only creates a
LearnerIdentity at account-*creation* time going forward — without this
migration, every pre-existing account (i.e. everyone, since nkowe_core was
just added) would 404 on LearnerDashboardView the first time they used it.

Purely additive: only creates rows for users that don't already have one.
Reverse is intentionally a no-op rather than a delete — by the time anyone
reverses this, new journeys/enrollments/record_events may already point at
the backfilled identities, and deleting them would cascade.
"""
from django.db import migrations


def create_missing_learner_identities(apps, schema_editor):
    CustomUser = apps.get_model('account', 'CustomUser')
    LearnerIdentity = apps.get_model('nkowe_core', 'LearnerIdentity')

    existing_user_ids = set(
        LearnerIdentity.objects.filter(user__isnull=False).values_list('user_id', flat=True)
    )
    to_create = [
        LearnerIdentity(user_id=user_id)
        for user_id in CustomUser.objects.exclude(id__in=existing_user_ids).values_list('id', flat=True)
    ]
    LearnerIdentity.objects.bulk_create(to_create)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nkowe_core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_missing_learner_identities, noop_reverse),
    ]
