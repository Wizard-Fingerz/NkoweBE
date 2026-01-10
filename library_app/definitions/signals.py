import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Genre

@receiver(post_migrate)
def create_genres_from_file(sender, **kwargs):
    # Only run for the library_app app
    if sender.name != "library_app":
        return

    # 'genres.txt' should be located in the same directory as this signals.py file
    file_path = os.path.join(os.path.dirname(__file__), 'genres.txt')
    if not os.path.exists(file_path):
        print(f"[Genre Loader] File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            # Skip empty or comment lines
            if not line or line.startswith("#"):
                continue
            try:
                # Split line into name and (optional) description
                parts = [p.strip() for p in line.split(',', 1)]
                name = parts[0]
                description = parts[1] if len(parts) > 1 else ""
                Genre.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
            except Exception as e:
                print(f"[Genre Loader] Error on line {line_num}: {line} ({e})")