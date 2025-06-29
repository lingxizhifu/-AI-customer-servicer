from django.apps import AppConfig


class CustomerServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "customer_service"

    def ready(self):
        import customer_service.signals
