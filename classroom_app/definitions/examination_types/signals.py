import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import ExaminationType

@receiver(post_migrate)
def create_examination_types_from_file(sender, **kwargs):
    # Run only for the app containing the ExaminationType model
    if sender.name != 'classroom_app':  # Replace 'classroom_app' with your app's name
        return

    file_path = os.path.join(os.path.dirname(__file__), 'examination_types.txt')
    
    if not os.path.exists(file_path):
        print(f"[Examination Type Loader] File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, start=1):
            # Skip empty or comment lines
            if not line.strip() or line.strip().startswith("#"):
                continue
            
            try:
                # Split line by comma and strip extra spaces
                name, description, level, region = map(str.strip, line.strip().split(','))
                
                # Create or get the ExaminationType object
                ExaminationType.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'level': level,
                        'region': region
                    }
                )
            except ValueError:
                print(f"[Examination Type Loader] Line {line_num} is invalid: {line.strip()}")
