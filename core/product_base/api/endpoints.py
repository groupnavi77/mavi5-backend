from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from ninja_extra.pagination import (
    paginate, 
    PaginatedResponseSchema, 
    PageNumberPaginationExtra
)
from enum import Enum

from core.product_base.api.services import ProductBaseService
from core.product_base.api.filters import ProductBaseFilter, ProductBaseFilterSecondary
from core.product_base.api.schemas import ProductBaseOut, ProductBaseListOut
from core.product_base.models import ProductBase

router = Router()

# 📊 Enum para el dropdown de ordenamiento
class ProductBaseOrderBy(str, Enum):
    """Opciones de ordenamiento para ProductBase"""
    NEWEST = "-created_at"
    OLDEST = "created_at"
    TITLE_ASC = "title"
    TITLE_DESC = "-title"
    RECENTLY_UPDATED = "-updated_at"
    LEAST_UPDATED = "updated_at"

# 📄 Configuración de paginación
class ProductBasePagination(PageNumberPaginationExtra):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


# 📋 ENDPOINT: Listar productos base con filtros y paginación
@router.get(
    "/list", 
    response=PaginatedResponseSchema[ProductBaseListOut],
    summary="Listar productos base",
    description="Lista productos base con filtros, ordenamiento y paginación"
)
@paginate(ProductBasePagination, filter_schema=ProductBaseFilter)
def list_products(
    request,
    order_by: ProductBaseOrderBy = ProductBaseOrderBy.NEWEST
):
    """
    Lista productos base con filtros y paginación.
    
    Parámetros disponibles:
    - order_by: Ordenamiento (dropdown)
      * NEWEST: Más recientes
      * OLDEST: Más antiguos
      * TITLE_ASC: Título A-Z
      * TITLE_DESC: Título Z-A
      * RECENTLY_UPDATED: Actualizados recientemente
      * LEAST_UPDATED: Menos actualizados
    
    - search: Búsqueda en título y descripción
    - category_id: ID de la categoría
    - tags: Tags separados por comas (ej: "economico,packaging")
    - published: true/false
    - price_min: Precio mínimo
    - price_max: Precio máximo
    - has_discount: true (con descuento) / false (sin descuento)
    - created_after: Fecha YYYY-MM-DD
    - created_before: Fecha YYYY-MM-DD
    
    Ejemplos:
    - /api/product-base/list?order_by=NEWEST
    - /api/product-base/list?search=tarjeta&has_discount=true
    - /api/product-base/list?price_min=10&price_max=50&category_id=1
    """
    queryset = ProductBaseService.list_products(use_cache=True).order_by(order_by.value)
    return queryset


# 🔍 ENDPOINT: Obtener producto base por ID
@router.get(
    "/{product_id}",
    response=ProductBaseOut,
    summary="Detalle del producto base",
    description="Obtiene el detalle completo de un producto base por ID"
)
def get_product(request, product_id: int):
    """
    Obtiene un producto base específico por ID con toda su información.
    
    Incluye:
    - Información básica
    - Categoría
    - Galería de imágenes
    - Tabla completa de precios
    - Descuentos activos e inactivos
    - Tags
    - Rango de precios
    """
    product = ProductBaseService.get_product_by_id(product_id, use_cache=True)
        
    return product


# 🔑 ENDPOINT: Obtener producto base por slug
@router.get(
    "/by-slug/{slug}",
    response=ProductBaseOut,
    summary="Detalle del producto base por slug",
    description="Obtiene el detalle completo por slug (SEO-friendly)"
)
def get_product_by_slug(request, slug: str):
    """
    Obtiene un producto base por su slug.
    Ideal para URLs amigables tipo: /productos/tarjetas-de-presentacion
    """
    product =  ProductBaseService.get_product_by_slug(slug, use_cache=True)

    return product


# 🔑 ENDPOINT: Obtener producto base por key
@router.get(
    "/by-key/{key}",
    response=ProductBaseOut,
    summary="Detalle del producto base por key",
    description="Obtiene el detalle completo por key interna"
)
def get_product_by_key(request, key: str):
    """Obtiene un producto base por su key única."""
    product = get_object_or_404(
        ProductBaseService.get_optimized_queryset(),
        key=key,
        published=True
    )
    return product

# 📁 ENDPOINT: Productos de una categoría por slug
@router.get(
    "/category/{category_slug}",
    response=PaginatedResponseSchema[ProductBaseListOut],
    summary="Productos por slug",
    description="Lista productos de una categoría específica"
)
@paginate(ProductBasePagination, filter_schema=ProductBaseFilterSecondary)
def list_products_by_category_slug(
    request,
    category_slug: str,
    order_by: ProductBaseOrderBy = ProductBaseOrderBy.NEWEST
):
    """Lista productos de una categoría específica."""
    return (
        ProductBaseService.list_products()
        .filter(category__slug=category_slug)
        .order_by(order_by.value)
    )


# 🏷️ ENDPOINT: Productos por tag
@router.get(
    "/tag/{tag_name}",
    response=PaginatedResponseSchema[ProductBaseListOut],
    summary="Productos por tag",
    description="Lista productos con un tag específico"
)
@paginate(ProductBasePagination)
def list_products_by_tag(
    request,
    tag_name: str,
    order_by: ProductBaseOrderBy = ProductBaseOrderBy.NEWEST
):
    """Lista productos con un tag específico."""
    return (
        ProductBaseService.list_products()
        .filter(tag__name__iexact=tag_name)
        .distinct()
        .order_by(order_by.value)
    )


# 🎁 ENDPOINT: Productos con descuento
@router.get(
    "/discounted",
    response=PaginatedResponseSchema[ProductBaseListOut],
    summary="Productos con descuento",
    description="Lista solo productos que tienen descuentos activos"
)
@paginate(ProductBasePagination)
def list_discounted_products(
    request,
    order_by: ProductBaseOrderBy = ProductBaseOrderBy.NEWEST
):
    """
    Lista productos que tienen descuentos activos.
    Útil para sección de ofertas/promociones.
    """
    from django.utils import timezone
    now = timezone.now()
    
    return (
        ProductBaseService.list_products()
        .filter(
            product_base_discounts__discount__gt=0,
            product_base_discounts__start_date__lte=now,
            product_base_discounts__expiration_date__gte=now
        )
        .distinct()
        .order_by(order_by.value)
    )


# 📊 ENDPOINT: Listar todos los tags disponibles
@router.get(
    "/tags/all",
    response=List[str],
    summary="Listar todos los tags",
    description="Obtiene lista de todos los tags únicos"
)
def list_all_tags(request):
    """
    Lista todos los tags únicos usados en productos base.
    Útil para poblar filtros en el frontend.
    """
    from taggit.models import Tag
    tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__model='productbase'
    ).distinct().values_list('name', flat=True)
    return list(tags)