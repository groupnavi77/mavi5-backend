from typing import Annotated, Optional
from ninja import FilterSchema
from ninja.filter_schema import FilterLookup
from django.db.models import Q, Min, Max
from decimal import Decimal

class ProductBaseFilter(FilterSchema):
    """
    Esquema de filtros para ProductBase con soporte para precios y descuentos.
    
    Filtros disponibles:
    - search: Búsqueda en título y descripción
    - category_id: Filtro por categoría
    - tags: Filtro por tags (separados por comas)
    - published: Filtro por estado de publicación
    - slug: Slug exacto del producto
    - price_min: Precio mínimo
    - price_max: Precio máximo
    - has_discount: Productos con descuento activo
    - created_after: Productos creados después de una fecha
    - created_before: Productos creados antes de una fecha
    """
    
    # 🔍 Búsqueda de texto en título y descripción corta
    search: Optional[str] = None
    
    # 📁 Filtro por categoría
    category_slug: Annotated[
        Optional[str],
        FilterLookup("category__slug")
    ] = None
    
    # 🏷️ Filtro por tags
    tags: Optional[str] = None  # Formato: "tag1,tag2,tag3"
    
    # ✅ Filtro por estado de publicación
    published: Annotated[
        Optional[bool],
        FilterLookup("published")
    ] = None
    
    # 🔑 Slug exacto
    slug: Annotated[
        Optional[str],
        FilterLookup("slug__iexact")
    ] = None
    
    # 💰 Filtros de precio (estos requieren lógica especial)
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    
    # 🎁 Filtro para productos con descuento
    has_discount: Optional[bool] = None
    
    # 📅 Filtro por rango de fechas
    created_after: Annotated[
        Optional[str],  # Formato: "YYYY-MM-DD"
        FilterLookup("created_at__gte")
    ] = None
    
    created_before: Annotated[
        Optional[str],  # Formato: "YYYY-MM-DD"
        FilterLookup("created_at__lte")
    ] = None
    
    def filter_search(self, value):
        """
        Búsqueda en título y short_description.
        """
        if value:
            return Q(
                Q(title__icontains=value) | 
                Q(short_description__icontains=value)
            )
        return Q()
    
    def filter_tags(self, value):
        """
        Filtro personalizado para tags.
        """
        if value:
            tag_list = [t.strip() for t in value.split(',')]
            return Q(tag__name__in=tag_list)
        return Q()
    
    def filter_price_min(self, value):
        """
        Filtro para precio mínimo.
        Busca productos que tengan al menos un precio >= price_min.
        """
        if value:
            return Q(product_base_prices__price__gte=value)
        return Q()
    
    def filter_price_max(self, value):
        """
        Filtro para precio máximo.
        Busca productos que tengan al menos un precio <= price_max.
        """
        if value:
            return Q(product_base_prices__price__lte=value)
        return Q()
    
    def filter_has_discount(self, value):
        """
        Filtro para productos con descuento activo.
        """
        if value is True:
            # Tiene al menos un descuento con discount > 0
            return Q(
                product_base_discounts__discount__gt=0,
                product_base_discounts__isnull=False
            )
        elif value is False:
            # No tiene descuentos o todos son 0
            return Q(
                Q(product_base_discounts__isnull=True) |
                Q(product_base_discounts__discount=0)
            )
        return Q()
    
    def filter(self, queryset):
        """
        Método principal que aplica todos los filtros.
        """
        # 1. Aplicar filtros base
        queryset = super().filter(queryset)
        
        # 2. Aplicar distinct si es necesario (para evitar duplicados por JOINs)
        if self.tags or self.price_min or self.price_max or self.has_discount:
            queryset = queryset.distinct()
        
        return queryset
    

class ProductBaseFilterSecondary(FilterSchema):
    """
    Esquema de filtros para ProductBase con soporte para precios y descuentos.
    
    Filtros disponibles:
    - search: Búsqueda en título y descripción
    - tags: Filtro por tags (separados por comas)
    - slug: Slug exacto del producto
    - price_min: Precio mínimo
    - price_max: Precio máximo
    - has_discount: Productos con descuento activo
    - created_after: Productos creados después de una fecha
    - created_before: Productos creados antes de una fecha
    """
    
    # 🔍 Búsqueda de texto en título y descripción corta
    search: Optional[str] = None  
    
    # 🏷️ Filtro por tags
    tags: Optional[str] = None  # Formato: "tag1,tag2,tag3"
    
    # 🔑 Slug exacto
    slug: Annotated[
        Optional[str],
        FilterLookup("slug__iexact")
    ] = None
    
    # 💰 Filtros de precio (estos requieren lógica especial)
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    
    # 🎁 Filtro para productos con descuento
    has_discount: Optional[bool] = None
    
    # 📅 Filtro por rango de fechas
    created_after: Annotated[
        Optional[str],  # Formato: "YYYY-MM-DD"
        FilterLookup("created_at__gte")
    ] = None
    
    created_before: Annotated[
        Optional[str],  # Formato: "YYYY-MM-DD"
        FilterLookup("created_at__lte")
    ] = None
    
    def filter_search(self, value):
        """
        Búsqueda en título y short_description.
        """
        if value:
            return Q(
                Q(title__icontains=value) | 
                Q(short_description__icontains=value)
            )
        return Q()
    
    def filter_tags(self, value):
        """
        Filtro personalizado para tags.
        """
        if value:
            tag_list = [t.strip() for t in value.split(',')]
            return Q(tag__name__in=tag_list)
        return Q()
    
    def filter_price_min(self, value):
        """
        Filtro para precio mínimo.
        Busca productos que tengan al menos un precio >= price_min.
        """
        if value:
            return Q(product_base_prices__price__gte=value)
        return Q()
    
    def filter_price_max(self, value):
        """
        Filtro para precio máximo.
        Busca productos que tengan al menos un precio <= price_max.
        """
        if value:
            return Q(product_base_prices__price__lte=value)
        return Q()
    
    def filter_has_discount(self, value):
        """
        Filtro para productos con descuento activo.
        """
        if value is True:
            # Tiene al menos un descuento con discount > 0
            return Q(
                product_base_discounts__discount__gt=0,
                product_base_discounts__isnull=False
            )
        elif value is False:
            # No tiene descuentos o todos son 0
            return Q(
                Q(product_base_discounts__isnull=True) |
                Q(product_base_discounts__discount=0)
            )
        return Q()
    
    def filter(self, queryset):
        """
        Método principal que aplica todos los filtros.
        """
        # 1. Aplicar filtros base
        queryset = super().filter(queryset)
        
        # 2. Aplicar distinct si es necesario (para evitar duplicados por JOINs)
        if self.tags or self.price_min or self.price_max or self.has_discount:
            queryset = queryset.distinct()
        
        return queryset
    
    