from django.db import IntegrityError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os
from .models import InstitutionType
from django.db import IntegrityError

@receiver(post_migrate)
def create_system_defined_entries(sender, **kwargs):
    if sender.name == 'classroom_app':
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'institution_types.txt')
        with open(file_path, 'r') as file:
            for line in file:
                name = line.strip().lower()
                try:
                    InstitutionType.objects.get_or_create(
                        name=name,
                    )
                except IntegrityError:
                    pass