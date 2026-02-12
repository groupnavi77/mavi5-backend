from typing import Annotated, Optional
from ninja import FilterSchema
from ninja.filter_schema import FilterLookup
from django.db.models import Q
from enum import Enum

class ProductFilter(FilterSchema):
    """
    Esquema de filtros para productos - VERSIÓN SIMPLE SIN ORDER_BY.
    El ordenamiento se maneja directamente en el endpoint.
    """
    
    # 🔍 Búsqueda de texto en descripción
    search: Annotated[
        Optional[str], 
        FilterLookup("description__icontains")
    ] = None
    
    # ✅ Filtro por estado de publicación
    published: Annotated[
        Optional[bool], 
        FilterLookup("published")
    ] = None
    
    # 👤 Filtro por usuario
    user_id: Annotated[
        Optional[int], 
        FilterLookup("user_id")
    ] = None
    
    # 📦 Filtro por ProductBase
    product_base_id: Annotated[
        Optional[int], 
        FilterLookup("Product_base_id")
    ] = None
    
    # 🏷️ Filtro por tags (usando taggit)
    tags: Optional[str] = None  # Formato: "tag1,tag2,tag3"
    
    # 📅 Filtro por rango de fechas
    created_after: Annotated[
        Optional[str],
        FilterLookup("created_at__gte")
    ] = None
    
    created_before: Annotated[
        Optional[str],
        FilterLookup("created_at__lte")
    ] = None
    
    # 🔑 Búsqueda por key exacta
    key: Annotated[
        Optional[str],
        FilterLookup("key__iexact")
    ] = None
    
    def filter_tags(self, value):
        """Filtro personalizado para tags"""
        if value:
            tag_list = [t.strip() for t in value.split(',')]
            return Q(tag__name__in=tag_list)
        return Q()
    
    def filter(self, queryset):
        """Aplicar filtros y distinct para tags"""
        queryset = super().filter(queryset)
        
        # Aplicar distinct si se filtró por tags
        if self.tags:
            queryset = queryset.distinct()
        
        return queryset
    
# Productos por tag
class TagFilterMode(str, Enum):
    """Modo de filtrado de tags"""
    ALL = "all"  # Debe tener TODOS los tags (AND)
    ANY = "any"  # Debe tener AL MENOS UNO (OR)

# 📊 Enum para el dropdown de ordenamiento
class ProductOrderBy(str, Enum):
    """Opciones de ordenamiento para productos (aparece como dropdown en Swagger)"""
    NEWEST = "-created_at"
    OLDEST = "created_at"
    RECENTLY_UPDATED = "-updated_at"
    LEAST_UPDATED = "updated_at"
    KEY_ASCENDING = "key"
    KEY_DESCENDING = "-key"
    ID_ASCENDING = "id"
    ID_DESCENDING = "-id"