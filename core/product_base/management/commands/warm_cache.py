"""
Comando para pre-calentar el caché con los productos más importantes.
Uso: python manage.py warm_cache
"""

from django.core.management.base import BaseCommand
from core.product_base.api.services import ProductBaseService
from core.product_base.models import ProductBase


class Command(BaseCommand):
    help = 'Pre-calienta el caché con los productos más importantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar todo el caché antes',
        )
        parser.add_argument(
            '--top',
            type=int,
            default=50,
            help='Número de productos a cachear (default: 50)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🗑️  Limpiando caché...')
            ProductBaseService.clear_all_cache()
            self.stdout.write(self.style.SUCCESS('   ✓ Caché limpiado\n'))

        self.stdout.write('🔥 Calentando caché...')
        
        # 1. Cachear lista principal
        self.stdout.write('   → Lista principal...')
        ProductBaseService.list_products(use_cache=False)
        self.stdout.write(self.style.SUCCESS('   ✓ Lista cacheada'))
        
        # 2. Cachear productos más recientes
        top_count = options['top']
        self.stdout.write(f'   → Top {top_count} productos...')
        
        recent_products = ProductBase.objects.filter(
            published=True
        ).order_by('-created_at')[:top_count]
        
        for i, product in enumerate(recent_products, 1):
            ProductBaseService.get_product_by_id(product.id, use_cache=False)
            ProductBaseService.get_product_by_slug(product.slug, use_cache=False)
            
            if i % 10 == 0:
                self.stdout.write(f'   {i}/{top_count} cacheados...')
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ {top_count} productos cacheados'))
        
        # 3. Estadísticas
        stats = ProductBaseService.get_cache_stats()
        self.stdout.write('\n📊 Estadísticas:')
        for key, is_cached in stats.items():
            status = '✓' if is_cached else '✗'
            self.stdout.write(f'   {status} {key}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Caché pre-calentado exitosamente\n'))