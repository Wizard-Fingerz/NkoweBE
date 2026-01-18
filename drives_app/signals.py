from django.db.models.signals import post_save, post_migrate
from django.conf import settings
from django.dispatch import receiver
from django.apps import apps
from django.db.models import Q
from django.db import transaction
from django.core.management.color import no_style
from drives_app.models import DriveFolder

DEFAULT_FOLDERS = [
    ('Documents', True),
    ('Musics', True),
    ('Videos', True),
    ('Pictures', True),
    ('Images', True),
    ('Recent', True),
]

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_drive_folders(sender, instance, created, **kwargs):
    if created:
        for folder_name, is_default in DEFAULT_FOLDERS:
            DriveFolder.objects.get_or_create(
                owner=instance,
                name=folder_name,
                parent=None,
                defaults={'is_default': is_default}
            )

@receiver(post_migrate)
def create_missing_drive_folders_for_existing_users(sender, **kwargs):
    """
    Run after migrations to create default drive folders for users missing them.
    This can be connected to the post_migrate signal.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL)
    for user in User.objects.all():
        for folder_name, is_default in DEFAULT_FOLDERS:
            if not DriveFolder.objects.filter(owner=user, name=folder_name, parent=None).exists():
                DriveFolder.objects.create(
                    owner=user,
                    name=folder_name,
                    parent=None,
                    is_default=is_default
                )

