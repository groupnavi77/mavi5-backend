# core/category/api/endpoints.py

from ninja import Router, Query
from ninja.pagination import paginate, PageNumberPagination
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count

from ..models import Category
from .schemas import (
    CategorySchema, 
    CategoryDetailSchema, 
    CategoryTreeSchema,
    CategoryCreateSchema,
    CategoryUpdateSchema,
    CategoryFilterSchema
)
from .services import CategoryService
from app.auth import jwt_auth

router = Router(tags=['Categorías'])

# Inicializar servicio
category_service = CategoryService()


# ==============================================================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# ==============================================================================

@router.get('/', response=List[CategorySchema])
@paginate(PageNumberPagination, page_size=50)
def list_categories(
    request,
    filters: CategoryFilterSchema = Query(...)
):
    """
    Lista todas las categorías con filtros opcionales.
    
    Filtros disponibles:
    - search: Buscar por título o descripción
    - parent_id: Filtrar por categoría padre
    - level: Filtrar por nivel en el árbol (0=raíz, 1=hijos directos, etc)
    - has_children: true/false - Solo categorías con/sin hijos
    - root_only: true/false - Solo categorías raíz
    """
    return category_service.get_all_categories(
        search=filters.search,
        parent_id=filters.parent_id,
        level=filters.level,
        has_children=filters.has_children,
        root_only=filters.root_only,
        ordering=filters.ordering
    )


@router.get('/tree', response=List[CategoryTreeSchema])
def get_category_tree(request, parent_id: Optional[int] = None):
    """
    Obtiene el árbol completo de categorías en formato jerárquico.
    
    Si se proporciona parent_id, obtiene el subárbol desde ese nodo.
    Usa caché automáticamente para mejor rendimiento.
    """
    return category_service.get_tree(parent_id=parent_id, use_cache=True)


@router.get('/roots', response=List[CategorySchema])
def get_root_categories(request):
    """
    Obtiene solo las categorías raíz (nivel 0).
    Útil para menús principales.
    """
    return Category.objects.filter(level=0).order_by('title')


@router.get('/breadcrumb/{category_id}', response=List[CategorySchema])
def get_breadcrumb(request, category_id: int):
    """
    Obtiene la ruta de navegación (breadcrumb) para una categoría.
    Retorna la categoría y todos sus ancestros hasta la raíz.
    
    Ejemplo: Inicio > Electrónica > Celulares > Smartphones
    """
    category = get_object_or_404(Category, id=category_id)
    # get_ancestors incluye desde la raíz hasta el padre
    ancestors = list(category.get_ancestors())
    # Agregar la categoría actual
    breadcrumb = ancestors + [category]
    return breadcrumb


@router.get('/{category_id}', response=CategoryDetailSchema)
def get_category(request, category_id: int):
    """
    Obtiene los detalles completos de una categoría específica.
    Incluye información de padre, hijos y estadísticas.
    """
    category = get_object_or_404(Category, id=category_id)
    
    # Obtener hijos directos
    children = category.get_children()
    
    # Obtener hermanos (categorías al mismo nivel con el mismo padre)
    siblings = category.get_siblings(include_self=False)
    
    # Contar productos (si tienes relación con productos)
    # products_count = category.products.count()  # Descomentar si aplica
    
    return {
        'id': category.id,
        'title': category.title,
        'slug': category.slug,
        'icon': category.icon,
        'description': category.description,
        'cat_image_url': category.cat_image.url if category.cat_image else None,
        'level': category.level,
        'parent_id': category.parent_id,
        'parent': {
            'id': category.parent.id,
            'title': category.parent.title,
            'slug': category.parent.slug,
        } if category.parent else None,
        'children': [
            {
                'id': child.id,
                'title': child.title,
                'slug': child.slug,
                'icon': child.icon,
            }
            for child in children
        ],
        'siblings': [
            {
                'id': sibling.id,
                'title': sibling.title,
                'slug': sibling.slug,
            }
            for sibling in siblings
        ],
        'children_count': children.count(),
        'descendants_count': category.get_descendant_count(),
        # 'products_count': products_count,  # Descomentar si aplica
    }


@router.get('/slug/{slug}', response=CategoryDetailSchema)
def get_category_by_slug(request, slug: str):
    """
    Obtiene una categoría por su slug.
    Útil para URLs amigables.
    """
    category = get_object_or_404(Category, slug=slug)
    
    children = category.get_children()
    siblings = category.get_siblings(include_self=False)
    
    return {
        'id': category.id,
        'title': category.title,
        'slug': category.slug,
        'icon': category.icon,
        'description': category.description,
        'cat_image_url': category.cat_image.url if category.cat_image else None,
        'level': category.level,
        'parent_id': category.parent_id,
        'parent': {
            'id': category.parent.id,
            'title': category.parent.title,
            'slug': category.parent.slug,
        } if category.parent else None,
        'children': [
            {
                'id': child.id,
                'title': child.title,
                'slug': child.slug,
                'icon': child.icon,
            }
            for child in children
        ],
        'siblings': [
            {
                'id': sibling.id,
                'title': sibling.title,
                'slug': sibling.slug,
            }
            for sibling in siblings
        ],
        'children_count': children.count(),
        'descendants_count': category.get_descendant_count(),
    }


@router.get('/{category_id}/children', response=List[CategorySchema])
def get_category_children(request, category_id: int):
    """
    Obtiene los hijos directos de una categoría.
    """
    category = get_object_or_404(Category, id=category_id)
    return category.get_children()


@router.get('/{category_id}/descendants', response=List[CategorySchema])
def get_category_descendants(request, category_id: int):
    """
    Obtiene todos los descendientes de una categoría (hijos, nietos, etc.).
    """
    category = get_object_or_404(Category, id=category_id)
    return category.get_descendants()


# ==============================================================================
# ENDPOINTS PROTEGIDOS (Requieren autenticación)
# ==============================================================================

@router.post('/', auth=jwt_auth, response={201: CategorySchema, 400: dict})
def create_category(request, payload: CategoryCreateSchema):
    """
    Crea una nueva categoría.
    Requiere autenticación.
    """
    category, error = category_service.create_category(
        title=payload.title,
        slug=payload.slug,
        parent_id=payload.parent_id,
        icon=payload.icon,
        description=payload.description
    )
    
    if error:
        return 400, {"error": error}
    
    return 201, category


@router.put('/{category_id}', auth=jwt_auth, response={200: CategorySchema, 400: dict, 404: dict})
def update_category(request, category_id: int, payload: CategoryUpdateSchema):
    """
    Actualiza una categoría existente.
    Requiere autenticación.
    """
    category, error = category_service.update_category(
        category_id=category_id,
        **payload.dict(exclude_unset=True)
    )
    
    if error:
        if "no encontrada" in error.lower():
            return 404, {"error": error}
        return 400, {"error": error}
    
    return 200, category


@router.delete('/{category_id}', auth=jwt_auth, response={200: dict, 400: dict, 404: dict})
def delete_category(request, category_id: int, force: bool = False):
    """
    Elimina una categoría.
    
    IMPORTANTE: 
    - Por defecto, no elimina si tiene subcategorías
    - Usa ?force=true para eliminar todo el subárbol (CASCADE)
    
    Requiere autenticación.
    """
    success, error = category_service.delete_category(category_id, force=force)
    
    if not success:
        if "no encontrada" in error.lower():
            return 404, {"error": error}
        return 400, {"error": error}
    
    return 200, {"success": True, "message": "Categoría eliminada exitosamente"}


@router.post('/{category_id}/move', auth=jwt_auth, response=CategorySchema)
def move_category(request, category_id: int, new_parent_id: Optional[int] = None):
    """
    Mueve una categoría a otro padre en el árbol.
    
    Si new_parent_id es None, la categoría se convierte en raíz.
    Requiere autenticación.
    """
    category = get_object_or_404(Category, id=category_id)
    
    if new_parent_id:
        new_parent = get_object_or_404(Category, id=new_parent_id)
        
        # Verificar que no se esté moviendo a sí misma o a un descendiente
        if new_parent == category or new_parent in category.get_descendants():
            return 400, {
                "error": "No se puede mover una categoría a sí misma o a un descendiente"
            }
        
        category.move_to(new_parent, 'last-child')
    else:
        # Mover a raíz
        category.parent = None
        category.save()
    
    return category


# ==============================================================================
# ENDPOINTS DE ESTADÍSTICAS
# ==============================================================================

@router.get('/stats/summary', response=dict)
def get_categories_stats(request):
    """
    Obtiene estadísticas generales de las categorías.
    Usa caché automáticamente.
    """
    return category_service.get_statistics()