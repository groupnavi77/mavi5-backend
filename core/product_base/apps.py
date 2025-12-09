from django.apps import AppConfig


class ProductConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.product_base'

    def ready(self):
        # Importar signals para que se registren automáticamente
        import core.product_base.api.services
