"""
Comando para ver estadísticas del caché.
Uso: python manage.py cache_stats
"""

from django.core.management.base import BaseCommand
from core.product_base.api.services import ProductBaseService


class Command(BaseCommand):
    help = 'Muestra estadísticas del caché'

    def handle(self, *args, **options):
        self.stdout.write('📊 Estadísticas de Caché\n')
        
        stats = ProductBaseService.get_cache_stats()
        
        cached_count = sum(1 for v in stats.values() if v)
        total_count = len(stats)
        
        if total_count > 0:
            hit_rate = cached_count / total_count * 100
        else:
            hit_rate = 0
        
        self.stdout.write(f'Total de claves: {total_count}')
        self.stdout.write(f'En caché: {cached_count}')
        self.stdout.write(f'Hit rate: {hit_rate:.1f}%\n')
        
        self.stdout.write('Detalle:')
        for key, is_cached in stats.items():
            if is_cached:
                status = self.style.SUCCESS('✓ CACHED')
            else:
                status = self.style.ERROR('✗ NOT CACHED')
            
            # Mostrar solo el final de la clave (más legible)
            short_key = key.split(':')[-1] if ':' in key else key
            self.stdout.write(f'  {short_key}: {status}')
        
        self.stdout.write('')