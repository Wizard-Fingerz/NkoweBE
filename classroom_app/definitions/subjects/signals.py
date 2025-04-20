from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Subject
import os

@receiver(post_migrate)
def create_subjects_from_file(sender, **kwargs):
    # Ensure this runs only for the app containing the Subject model
    if sender.name != 'classroom_app.definitions.subjects':
        return

    file_path = os.path.join(os.path.dirname(__file__), 'subjects.txt')
    if not os.path.exists(file_path):
        print(f"Subjects file not found: {file_path}")
        return

    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines
            if not line.strip():
                continue

            # Parse the line (name, description, level, category)
            try:
                name, description, level, category = line.strip().split(',')
                Subject.objects.get_or_create(
                    name=name.strip(),
                    defaults={
                        'description': description.strip(),
                        'level': level.strip(),
                        'category': category.strip(),
                    }
                )
            except ValueError:
                print(f"Invalid line format: {line.strip()}")