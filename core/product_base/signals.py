from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Category

@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidar el caché cuando se modifica una categoría"""
    cache.delete('category_all_tree')
    cache.delete('category_all_tree_serialized')