from ninja import Query, Router
from typing import List
from django.shortcuts import get_object_or_404
from ninja_extra.pagination import (
    paginate, 
    PaginatedResponseSchema, 
    PageNumberPaginationExtra
)
from enum import Enum

from core.product_ins.api.services import ProductService
from core.product_ins.api.filters import ProductFilter, TagFilterMode, ProductOrderBy
from core.product_ins.api.schemas import ProductOut, ProductDetailOut
from core.product_ins.models import Product


router = Router()


# Configuración de paginación
class ProductPagination(PageNumberPaginationExtra):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


# ✅ SOLUCIÓN CON DROPDOWN: Usar Enum como tipo del parámetro
@router.get(
    "/list", 
    response=PaginatedResponseSchema[ProductOut],
    summary="Listar productos",
    description="Lista productos con filtros, ordenamiento y paginación"
)
@paginate(ProductPagination, filter_schema=ProductFilter)
def list_products(
    request,
    order_by: ProductOrderBy = ProductOrderBy.NEWEST  # 🎯 Enum = Dropdown en Swagger
):
    """
    Lista productos con filtros y paginación.
    
    Parámetros:
    - order_by: Campo de ordenamiento (dropdown con opciones)
      * NEWEST: Más recientes primero (-created_at)
      * OLDEST: Más antiguos primero (created_at)
      * RECENTLY_UPDATED: Recientemente actualizados (-updated_at)
      * LEAST_UPDATED: Menos actualizados (updated_at)
      * KEY_ASCENDING: Por key A-Z (key)
      * KEY_DESCENDING: Por key Z-A (-key)
    
    - search: Búsqueda en descripción
    - published: true/false
    - user_id: ID del usuario
    - product_base_id: ID del ProductBase
    - tags: tags separados por comas
    - created_after/before: Rango de fechas
    
    Ejemplos:
    - /api/products/list?order_by=NEWEST
    - /api/products/list?search=tarjeta&order_by=KEY_ASCENDING&published=true
    """
    # Aplicar ordenamiento usando el valor del Enum
    queryset = ProductService.list_products().order_by(order_by.value)
    
    return queryset


# Detalle de producto por ID
@router.get("/{product_id}", response=ProductDetailOut)
def get_product(request, product_id: int):
    """Obtiene un producto por ID"""
    product = get_object_or_404(
        ProductService.get_optimized_queryset(),
        id=product_id,
        published=True
    )
    return product


# Detalle de producto por Key
@router.get("/by-key/{key}", response=ProductDetailOut)
def get_product_by_key(request, key: str):
    """Obtiene un producto por su key única"""
    product = get_object_or_404(
        ProductService.get_optimized_queryset(),
        key=key,
        published=True
    )
    return product


# Productos de un usuario
@router.get("/user/{user_id}", response=PaginatedResponseSchema[ProductOut])
@paginate(ProductPagination, filter_schema=ProductFilter)
def list_user_products(
    request, 
    user_id: int,
    order_by: ProductOrderBy = ProductOrderBy.NEWEST  # 🎯 Dropdown
):
    """Lista productos de un usuario específico"""
    return (
        ProductService.list_products()
        .filter(user_id=user_id)
        .order_by(order_by.value)
    )



@router.get("/tags/filter", response=PaginatedResponseSchema[ProductOut])
@paginate(ProductPagination)
def list_products_by_tags_flexible(
    request,
    tags: List[str] = Query(..., description="Lista de tags para filtrar"),
    mode: TagFilterMode = Query(TagFilterMode.ANY, description="Modo de filtrado: 'all' (AND) o 'any' (OR)"),
    order_by: ProductOrderBy = ProductOrderBy.NEWEST
):
    """
    Lista productos filtrando por tags con modo seleccionable.
    
    Ejemplos:
    - GET /api/products/tags/filter?tags=oferta&tags=nuevo&mode=all
      → Productos que son OFERTA Y NUEVO
    
    - GET /api/products/tags/filter?tags=oferta&tags=nuevo&mode=any
      → Productos que son OFERTA O NUEVO
    
    - GET /api/products/tags/filter?tags=verano&tags=mujer&mode=all&order_by=price_low
      → Productos de VERANO Y MUJER, ordenados por precio ascendente
    """
    from django.db.models import Q
    
    queryset = ProductService.list_products()
    
    if mode == TagFilterMode.ALL:
        # Modo AND: debe tener TODOS los tags
        for tag in tags:
            queryset = queryset.filter(tag__name__iexact=tag)
    else:
        # Modo ANY: debe tener AL MENOS UNO
        tag_filter = Q()
        for tag in tags:
            tag_filter |= Q(tag__name__iexact=tag)
        queryset = queryset.filter(tag_filter)
    
    return queryset.distinct().order_by(order_by.value)


# Productos por ProductBase
@router.get("/base/{product_base_id}", response=PaginatedResponseSchema[ProductOut])
@paginate(ProductPagination)
def list_products_by_base(
    request, 
    product_base_id: int,
    order_by: ProductOrderBy = ProductOrderBy.NEWEST  # 🎯 Dropdown
):
    """Lista productos de un ProductBase específico"""
    return (
        ProductService.list_products()
        .filter(Product_base_id=product_base_id)
        .order_by(order_by.value)
    )


# 🏷️ BONUS: Endpoint para listar todos los tags disponibles
@router.get("/tags/all", response=List[str], summary="Listar todos los tags")
def list_all_tags(request):
    """
    Lista todos los tags únicos usados en productos.
    Útil para poblar filtros en el frontend.
    """
    from taggit.models import Tag
    tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__model='product'
    ).distinct().values_list('name', flat=True)
    return list(tags)