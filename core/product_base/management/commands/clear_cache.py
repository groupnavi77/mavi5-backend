"""
Comando para limpiar el caché de productos.
Uso: python manage.py clear_cache
"""

from django.core.management.base import BaseCommand
from core.product_base.api.services import ProductBaseService


class Command(BaseCommand):
    help = 'Limpia el caché de productos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            help='ID de producto específico a limpiar',
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')
        
        if product_id:
            self.stdout.write(f'🗑️  Limpiando caché del producto {product_id}...')
            ProductBaseService.invalidate_product_cache(product_id)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Caché del producto {product_id} limpiado\n')
            )
        else:
            self.stdout.write('🗑️  Limpiando TODO el caché...')
            ProductBaseService.clear_all_cache()
            self.stdout.write(self.style.SUCCESS('✅ Todo el caché limpiado\n'))