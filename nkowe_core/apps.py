from django.apps import AppConfig


class NkoweCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nkowe_core'
    verbose_name = 'Nkowe Core (Learner Identity, Journeys, Enrollment, Record)'

    def ready(self):
        import nkowe_core.signals  # noqa: F401 -- registers the signal receivers
