from django.apps import AppConfig


class DrivesAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drives_app'

    def ready(self):
        import drives_app.signals