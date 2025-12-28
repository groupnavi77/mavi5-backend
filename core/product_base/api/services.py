"""
Servicios optimizados para ProductBase con caché en MySQL.
Incluye invalidación automática mediante signals.
"""

from django.core.cache import cache
from django.db.models import QuerySet, Count, Min, Max, Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from core.product_base.models import ProductBase, Price, Discount

import hashlib
import json


class ProductBaseService:
    """
    Servicio optimizado con caché en MySQL.
    """
    
    # Tiempos de caché (en segundos)
    CACHE_LIST = 60 * 15  # 15 minutos
    CACHE_DETAIL = 60 * 60 * 24  # 24 horas
    
    @staticmethod
    def _get_cache_key(prefix: str, **kwargs) -> str:
        """Genera clave de caché única."""
        if kwargs:
            params_str = json.dumps(kwargs, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"mavi5:{prefix}:{params_hash}"
        return f"mavi5:{prefix}"
    
    @staticmethod
    def get_optimized_queryset() -> QuerySet[ProductBase]:
        """
        QuerySet base con todas las optimizaciones.
        """
        queryset = ProductBase.objects.all()
        
        return queryset
    
    @staticmethod
    def list_products(use_cache: bool = True) -> QuerySet[ProductBase]:
        """Lista productos publicados con caché."""
        cache_key = ProductBaseService._get_cache_key('products_list')
        
        if use_cache:
            cached_ids = cache.get(cache_key)
            
            if cached_ids is not None:
                return (
                    ProductBaseService.get_optimized_queryset()
                    .filter(id__in=cached_ids)
                    .order_by('-created_at')
                )
        
        queryset = (
            ProductBaseService.get_optimized_queryset()
            .filter(published=True)
            .order_by('-created_at')
        )
        
        if use_cache:
            product_ids = list(queryset.values_list('id', flat=True)[:1000])
            cache.set(cache_key, product_ids, ProductBaseService.CACHE_LIST)
        
        return queryset
    
    @staticmethod
    def get_product_by_id(product_id: int, use_cache: bool = True):
        """Obtiene un producto por ID con caché."""
        cache_key = ProductBaseService._get_cache_key('product_detail', id=product_id)
        
        if use_cache:
            cached_product = cache.get(cache_key)
            if cached_product is not None:
                return cached_product
        
        product = ProductBaseService.get_optimized_queryset().get(
            id=product_id,
            published=True
        )
        
        if use_cache:
            cache.set(cache_key, product, ProductBaseService.CACHE_DETAIL)
        
        return product
    
    @staticmethod
    def get_product_by_slug(slug: str, use_cache: bool = True):
        """Obtiene un producto por slug con caché."""
        cache_key = ProductBaseService._get_cache_key('product_slug', slug=slug)
        
        if use_cache:
            cached_product = cache.get(cache_key)
            if cached_product is not None:
                return cached_product
        
        product = ProductBaseService.get_optimized_queryset().get(
            slug=slug,
            published=True
        )
        
        if use_cache:
            cache.set(cache_key, product, ProductBaseService.CACHE_DETAIL)
        
        return product
    
    @staticmethod
    def get_product_by_key(key: str) -> ProductBase:
        """Obtiene un producto por key (sin caché)."""
        return ProductBaseService.get_optimized_queryset().get(key=key)
    
    @staticmethod
    def get_products_by_category(category_id: int, use_cache: bool = True):
        """Lista productos de una categoría con caché."""
        cache_key = ProductBaseService._get_cache_key('products_category', cat=category_id)
        
        if use_cache:
            cached_ids = cache.get(cache_key)
            if cached_ids is not None:
                return ProductBaseService.get_optimized_queryset().filter(
                    id__in=cached_ids
                ).order_by('-created_at')
        
        queryset = ProductBaseService.list_products(use_cache=False).filter(
            category_id=category_id
        )
        
        if use_cache:
            product_ids = list(queryset.values_list('id', flat=True)[:500])
            cache.set(cache_key, product_ids, ProductBaseService.CACHE_LIST)
        
        return queryset
    
    @staticmethod
    def invalidate_product_cache(product_id: int = None):
        """Invalida el caché de productos."""
        if product_id:
            cache.delete(ProductBaseService._get_cache_key('product_detail', id=product_id))
            
            try:
                product = ProductBase.objects.get(id=product_id)
                cache.delete(ProductBaseService._get_cache_key('product_slug', slug=product.slug))
                cache.delete(ProductBaseService._get_cache_key('products_category', cat=product.category_id))
            except ProductBase.DoesNotExist:
                pass
        
        cache.delete(ProductBaseService._get_cache_key('products_list'))
    
    @staticmethod
    def clear_all_cache():
        """Limpia TODO el caché."""
        cache.clear()
    
    @staticmethod
    def get_cache_stats():
        """Obtiene estadísticas del caché."""
        keys_to_check = [
            ProductBaseService._get_cache_key('products_list'),
        ]
        
        stats = {}
        for key in keys_to_check:
            stats[key] = cache.get(key) is not None
        
        return stats


# ==============================================================================
# SIGNALS PARA INVALIDAR CACHÉ AUTOMÁTICAMENTE
# ==============================================================================

@receiver(post_save, sender=ProductBase)
def invalidate_cache_on_save(sender, instance, **kwargs):
    """Invalida caché cuando se guarda un producto"""
    ProductBaseService.invalidate_product_cache(instance.id)


@receiver(post_delete, sender=ProductBase)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Invalida caché cuando se elimina un producto"""
    ProductBaseService.invalidate_product_cache(instance.id)


@receiver(post_save, sender=Price)
def invalidate_cache_on_price_change(sender, instance, **kwargs):
    """Invalida caché cuando cambian los precios"""
    ProductBaseService.invalidate_product_cache(instance.product.id)


@receiver(post_save, sender=Discount)
def invalidate_cache_on_discount_change(sender, instance, **kwargs):
    """Invalida caché cuando cambian los descuentos"""
    ProductBaseService.invalidate_product_cache(instance.product.id)