from django.apps import AppConfig


class ListingsConfig(AppConfig):
    name = 'listings'

    def ready(self):
        # Register model signal handlers (e.g., image file cleanup on delete).
        from . import signals  # noqa: F401
