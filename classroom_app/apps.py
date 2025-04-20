from django.apps import AppConfig


class ClassroomAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'classroom_app'

    def ready(self):
        import classroom_app.definitions.subjects.signals  # Import the signals
