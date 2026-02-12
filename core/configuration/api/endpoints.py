# core/configuration/api/endpoints.py - COMPLETO CON MENU Y PAGE

from ninja import Router
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from typing import List, Optional, Dict
from datetime import datetime

from ..models import Slider, Menu, Page
from .schemas import (
    SliderSchema, SliderListSchema, SliderStatsSchema,
    MenuSchema, MenuListSchema, MenuTreeSchema,
    PageListSchema, PageDetailSchema, PageSEOSchema
)

router = Router()


# ============================================================================
# ENDPOINTS DE SLIDER (YA EXISTENTES)
# ============================================================================

@router.get("/sliders/list", response=List[SliderListSchema])
def list_sliders(
    request,
    section: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = 'order',
    currently_active_only: Optional[bool] = False
):
    """Lista todos los sliders con filtros"""
    queryset = Slider.objects.all()
    
    if section:
        queryset = queryset.filter(section=section)
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(slug__icontains=search) |
            Q(content__icontains=search)
        )
    
    if currently_active_only:
        now = timezone.now()
        queryset = queryset.filter(
            is_active=True
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
    
    valid_order_fields = ['order', '-order', 'created_at', '-created_at', 'title', 'slug']
    if order_by in valid_order_fields:
        queryset = queryset.order_by(order_by)
    else:
        queryset = queryset.order_by('section', 'order')
    
    # Construir respuesta manualmente
    result = []
    for slider in queryset:
        result.append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,
            'section': slider.section,
            'section_display': slider.get_section_display(),
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'heading': slider.content.get('heading') if slider.content else None,
            'order': slider.order,
            'is_active': slider.is_active,
            'is_currently_active': slider.is_currently_active(),
        })
    
    return result


@router.get("/sliders/section/{section_name}", response=List[SliderSchema])
def get_sliders_by_section(request, section_name: str, include_inactive: bool = False):
    """Obtiene sliders de una sección específica"""
    now = timezone.now()
    queryset = Slider.objects.filter(section=section_name)
    
    if not include_inactive:
        queryset = queryset.filter(
            is_active=True
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
    
    queryset = queryset.order_by('order')
    
    # Construir respuesta manualmente
    result = []
    for slider in queryset:
        result.append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,
            'section': slider.section,
            'section_display': slider.get_section_display(),
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'content': slider.content,
            'order': slider.order,
            'is_active': slider.is_active,
            'start_date': slider.start_date,
            'end_date': slider.end_date,
            'created_at': slider.created_at,
            'updated_at': slider.updated_at,
        })
    
    return result


@router.get("/sliders/{slider_id}", response=SliderSchema)
def get_slider(request, slider_id: int):
    """Obtiene un slider por ID"""
    slider = get_object_or_404(Slider, id=slider_id)
    
    return {
        'id': slider.id,
        'title': slider.title,
        'slug': slider.slug,
        'section': slider.section,
        'section_display': slider.get_section_display(),
        'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
        'content': slider.content,
        'order': slider.order,
        'is_active': slider.is_active,
        'start_date': slider.start_date,
        'end_date': slider.end_date,
        'created_at': slider.created_at,
        'updated_at': slider.updated_at,
    }


@router.get("/sliders/slug/{slug}", response=SliderSchema)
def get_slider_by_slug(request, slug: str):
    """Obtiene un slider por slug"""
    slider = get_object_or_404(Slider, slug=slug)
    
    return {
        'id': slider.id,
        'title': slider.title,
        'slug': slider.slug,
        'section': slider.section,
        'section_display': slider.get_section_display(),
        'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
        'content': slider.content,
        'order': slider.order,
        'is_active': slider.is_active,
        'start_date': slider.start_date,
        'end_date': slider.end_date,
        'created_at': slider.created_at,
        'updated_at': slider.updated_at,
    }


# ============================================================================
# ENDPOINTS DE MENU (NUEVOS)
# ============================================================================

@router.get("/menus/list", response=List[MenuListSchema])
def list_menus(
    request,
    menu_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None
):
    """
    Lista todos los menús con filtros.
    
    Parámetros:
    - menu_type: Filtrar por tipo (header, footer, mobile, sidebar, custom)
    - is_active: true/false para filtrar activos
    - search: Buscar en nombre, slug o descripción
    """
    queryset = Menu.objects.all()
    
    if menu_type:
        queryset = queryset.filter(menu_type=menu_type)
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search) |
            Q(description__icontains=search)
        )
    
    queryset = queryset.order_by('menu_type', 'tree_id', 'lft')
    
    # Construir respuesta manualmente
    result = []
    for menu in queryset:
        result.append({
            'id': menu.id,
            'name': menu.name,
            'slug': menu.slug,
            'menu_type': menu.menu_type,
            'menu_type_display': menu.get_menu_type_display(),
            'link_type': menu.link_type,
            'url': menu.get_url(),
            'icon': menu.icon,
            'order': menu.order,
            'level': menu.level,
            'is_active': menu.is_active,
            'parent_id': menu.parent_id,
        })
    
    return result


@router.get("/menus/tree/{menu_type}", response=List[MenuTreeSchema])
def get_menu_tree(request, menu_type: str):
    """
    Obtiene el árbol completo de menús para un tipo específico.
    Solo retorna menús activos organizados jerárquicamente.
    
    Parámetros:
    - menu_type: Tipo de menú (header, footer, mobile, sidebar, custom)
    
    Ejemplos:
    GET /api/menus/tree/header
    GET /api/menus/tree/footer
    
    Response: Árbol jerárquico con children anidados
    """
    # Solo raíz activos
    roots = Menu.objects.filter(
        menu_type=menu_type,
        parent__isnull=True,
        is_active=True
    ).order_by('order')
    
    def build_tree(node):
        """Construye el árbol recursivamente"""
        children = node.get_active_children().order_by('order')
        return {
            'id': node.id,
            'name': node.name,
            'slug': node.slug,
            'url': node.get_url(),
            'icon': node.icon,
            'is_featured': node.is_featured,
            'level': node.level,
            'children': [build_tree(child) for child in children]
        }
    
    return [build_tree(root) for root in roots]

@router.get("/menus/{menu_id}", response=MenuSchema)
def get_menu(request, menu_id: int):
    """
    Obtiene detalles completos de un menú específico.
    
    Ejemplo:
    GET /api/menus/123
    """
    menu = get_object_or_404(Menu, id=menu_id)
    
    # ✅ CONSTRUIR CHILDREN CON TODOS LOS CAMPOS REQUERIDOS
    children = []
    for child in menu.get_active_children().order_by('order'):
        children.append({
            'id': child.id,
            'name': child.name,
            'slug': child.slug,
            'description': child.description or '',
            'menu_type': child.menu_type,
            'menu_type_display': child.get_menu_type_display(),
            'link_type': child.link_type,
            'link_type_display': child.get_link_type_display(),
            'url': child.get_url(),
            'category': child.category_id,
            'page': child.page_id,
            'icon': child.icon or '',
            'image': child.image.url if child.image else None,
            'image_url': child.image.url if child.image else None,
            'css_classes': getattr(child, 'css_classes', ''),
            'attributes': getattr(child, 'attributes', {}),
            'is_active': child.is_active,
            'is_featured': child.is_featured,
            'open_in_new_tab': child.open_in_new_tab,
            'order': child.order,
            'parent': child.parent_id,
            'level': child.level,
            'mega_menu_columns': getattr(child, 'mega_menu_columns', 1),
            'has_children': child.has_children(),
            'children': [],  # Sin recursión profunda
            'created_at': child.created_at,
            'updated_at': child.updated_at,
        })
    
    # ✅ CONSTRUIR DICT PRINCIPAL
    return {
        'id': menu.id,
        'name': menu.name,
        'slug': menu.slug,
        'description': menu.description or '',
        'menu_type': menu.menu_type,
        'menu_type_display': menu.get_menu_type_display(),
        'link_type': menu.link_type,
        'link_type_display': menu.get_link_type_display(),
        'url': menu.get_url(),
        'category': menu.category_id,
        'page': menu.page_id,
        'icon': menu.icon or '',
        'image': menu.image.url if menu.image else None,
        'image_url': menu.image.url if menu.image else None,
        'css_classes': getattr(menu, 'css_classes', ''),
        'attributes': getattr(menu, 'attributes', {}),
        'is_active': menu.is_active,
        'is_featured': menu.is_featured,
        'open_in_new_tab': menu.open_in_new_tab,
        'order': menu.order,
        'parent': menu.parent_id,
        'level': menu.level,
        'mega_menu_columns': getattr(menu, 'mega_menu_columns', 1),
        'has_children': menu.has_children(),
        'children': children,
        'created_at': menu.created_at,
        'updated_at': menu.updated_at,
    }


@router.get("/menus/slug/{slug}", response=MenuSchema)
def get_menu_by_slug(request, slug: str):
    """
    Obtiene un menú por slug.
    
    Ejemplo:
    GET /api/menus/slug/shop-now
    """
    menu = get_object_or_404(Menu, slug=slug)
    
    # ✅ CONSTRUIR CHILDREN CON TODOS LOS CAMPOS REQUERIDOS
    children = []
    for child in menu.get_active_children().order_by('order'):
        children.append({
            'id': child.id,
            'name': child.name,
            'slug': child.slug,
            'url': child.get_url(),
            'icon': child.icon or '',
            'level': child.level,
            'is_featured': menu.is_featured,
            'has_children': child.has_children(),
            'children': [],  # Sin recursión profunda
        })
    
    # ✅ CONSTRUIR DICT PRINCIPAL
    return {
        'id': menu.id,
        'name': menu.name,
        'slug': menu.slug,
        'url': menu.get_url(),
        'icon': menu.icon or '',
        'level': menu.level,
        'is_featured': menu.is_featured,
        'has_children': menu.has_children(),
        'children': children,
    }


@router.get("/menus/types/list", response=List[dict])
def list_menu_types(request):
    """
    Lista todos los tipos de menú con conteos.
    
    Ejemplo:
    GET /api/menus/types/list
    
    Response:
    [
        {
            "value": "header",
            "label": "Menú Principal (Header)",
            "count": 5,
            "active_count": 4
        }
    ]
    """
    types_data = []
    
    for type_value, type_label in Menu.MENU_TYPE_CHOICES:
        total_count = Menu.objects.filter(menu_type=type_value).count()
        active_count = Menu.objects.filter(
            menu_type=type_value,
            is_active=True
        ).count()
        
        if total_count > 0:
            types_data.append({
                'value': type_value,
                'label': type_label,
                'count': total_count,
                'active_count': active_count
            })
    
    return types_data


# ============================================================================
# ENDPOINTS DE PAGE (NUEVOS)
# ============================================================================

@router.get("/pages/list", response=List[PageListSchema])
def list_pages(
    request,
    page_type: Optional[str] = None,
    is_published: Optional[bool] = True,
    search: Optional[str] = None
):
    """Lista todas las páginas con filtros."""
    queryset = Page.objects.all()
    
    if page_type:
        queryset = queryset.filter(page_type=page_type)
    
    if is_published is not None:
        queryset = queryset.filter(is_published=is_published)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(slug__icontains=search) |
            Q(content__icontains=search) |
            Q(excerpt__icontains=search)
        )
    
    # Solo páginas publicadas actualmente
    now = timezone.now()
    queryset = queryset.filter(
        Q(published_at__isnull=True) | Q(published_at__lte=now)
    )
    
    queryset = queryset.order_by('page_type', 'order', 'title')
    
    # Construir respuesta manualmente
    result = []
    for page in queryset:
        result.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'page_type': page.page_type,
            'page_type_display': page.get_page_type_display(),
            'excerpt': page.excerpt,
            'featured_image_url': page.featured_image_url,
            'is_published': page.is_published,
            'published_at': page.published_at,
            'reading_time': page.get_reading_time(),
        })
    
    return result


@router.get("/pages/{page_id}", response=PageDetailSchema)
def get_page(request, page_id: int):
    """Obtiene detalles completos de una página."""
    page = get_object_or_404(Page, id=page_id, is_published=True)
    
    # Verificar autenticación si es requerida
    if page.require_auth and not request.user.is_authenticated:
        return {"error": "Autenticación requerida"}, 401
    
    return {
        'id': page.id,
        'title': page.title,
        'slug': page.slug,
        'page_type': page.page_type,
        'page_type_display': page.get_page_type_display(),
        'template': page.template,
        'template_display': page.get_template_display(),
        'content': page.content,
        'excerpt': page.excerpt,
        'featured_image_url': page.featured_image_url,
        'meta_title': page.meta_title,
        'meta_description': page.meta_description,
        'meta_keywords': page.meta_keywords,
        'is_published': page.is_published,
        'show_in_menu': page.show_in_menu,
        'require_auth': page.require_auth,
        'published_at': page.published_at,
        'created_at': page.created_at,
        'updated_at': page.updated_at,
        'reading_time': page.get_reading_time(),
        'absolute_url': page.get_absolute_url(),
    }


@router.get("/pages/slug/{slug}", response=PageDetailSchema)
def get_page_by_slug(request, slug: str):
    """Obtiene una página por slug."""
    page = get_object_or_404(Page, slug=slug, is_published=True)
    
    # Verificar autenticación si es requerida
    if page.require_auth and not request.user.is_authenticated:
        return {"error": "Autenticación requerida"}, 401
    
    return {
        'id': page.id,
        'title': page.title,
        'slug': page.slug,
        'page_type': page.page_type,
        'page_type_display': page.get_page_type_display(),
        'template': page.template,
        'template_display': page.get_template_display(),
        'content': page.content,
        'excerpt': page.excerpt,
        'featured_image_url': page.featured_image_url,
        'meta_title': page.meta_title,
        'meta_description': page.meta_description,
        'meta_keywords': page.meta_keywords,
        'is_published': page.is_published,
        'show_in_menu': page.show_in_menu,
        'require_auth': page.require_auth,
        'published_at': page.published_at,
        'created_at': page.created_at,
        'updated_at': page.updated_at,
        'reading_time': page.get_reading_time(),
        'absolute_url': page.get_absolute_url(),
    }


@router.get("/pages/type/{page_type}", response=List[PageListSchema])
def get_pages_by_type(request, page_type: str):
    """Obtiene todas las páginas de un tipo específico."""
    now = timezone.now()
    
    queryset = Page.objects.filter(
        page_type=page_type,
        is_published=True
    ).filter(
        Q(published_at__isnull=True) | Q(published_at__lte=now)
    ).order_by('order', 'title')
    
    # Construir respuesta manualmente
    result = []
    for page in queryset:
        result.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'page_type': page.page_type,
            'page_type_display': page.get_page_type_display(),
            'excerpt': page.excerpt,
            'featured_image_url': page.featured_image_url,
            'is_published': page.is_published,
            'published_at': page.published_at,
            'reading_time': page.get_reading_time(),
        })
    
    return result


@router.get("/pages/menu/footer", response=List[PageListSchema])
def get_footer_pages(request):
    """Obtiene páginas para mostrar en el footer."""
    now = timezone.now()
    
    queryset = Page.objects.filter(
        is_published=True,
        show_in_menu=True
    ).filter(
        Q(published_at__isnull=True) | Q(published_at__lte=now)
    ).order_by('page_type', 'order')
    
    # Construir respuesta manualmente
    result = []
    for page in queryset:
        result.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'page_type': page.page_type,
            'page_type_display': page.get_page_type_display(),
            'excerpt': page.excerpt,
            'featured_image_url': page.featured_image_url,
            'is_published': page.is_published,
            'published_at': page.published_at,
            'reading_time': page.get_reading_time(),
        })
    
    return result


@router.get("/pages/seo/{slug}", response=PageSEOSchema)
def get_page_seo(request, slug: str):
    """Obtiene solo la información SEO de una página."""
    page = get_object_or_404(Page, slug=slug, is_published=True)
    
    return {
        'title': page.title,
        'slug': page.slug,
        'meta_title': page.meta_title,
        'meta_description': page.meta_description,
        'meta_keywords': page.meta_keywords,
        'absolute_url': page.get_absolute_url(),
    }


@router.get("/pages/types/list", response=List[dict])
def list_page_types(request):
    """
    Lista todos los tipos de página con conteos.
    
    Ejemplo:
    GET /api/pages/types/list
    
    Response:
    [
        {
            "value": "legal",
            "label": "Legal",
            "count": 3
        }
    ]
    """
    types_data = []
    
    for type_value, type_label in Page.PAGE_TYPE_CHOICES:
        count = Page.objects.filter(
            page_type=type_value,
            is_published=True
        ).count()
        
        if count > 0:
            types_data.append({
                'value': type_value,
                'label': type_label,
                'count': count
            })
    
    return types_data


# ============================================================================
# ENDPOINT COMBINADO: CONFIGURACIÓN COMPLETA DEL SITIO
# ============================================================================

@router.get("/config/site", response=dict)
def get_site_config(request):
    """
    Obtiene toda la configuración del sitio en una sola llamada.
    Incluye menús, páginas para footer, estadísticas, etc.
    
    Ejemplo:
    GET /api/config/site
    
    Response:
    {
        "menus": {
            "header": [...],
            "footer": [...],
            "mobile": [...]
        },
        "footer_pages": [...],
        "stats": {
            "total_menus": 10,
            "total_pages": 5
        }
    }
    """
    now = timezone.now()
    
    # Menús por tipo
    menus = {}
    for menu_type, _ in Menu.MENU_TYPE_CHOICES:
        roots = Menu.objects.filter(
            menu_type=menu_type,
            parent__isnull=True,
            is_active=True
        ).order_by('order')
        
        if roots.exists():
            def build_tree(node):
                children = node.get_active_children().order_by('order')
                return {
                    'id': node.id,
                    'name': node.name,
                    'slug': node.slug,
                    'url': node.get_url(),
                    'icon': node.icon,
                    'is_featured': node.is_featured,
                    'children': [build_tree(child) for child in children]
                }
            
            menus[menu_type] = [build_tree(root) for root in roots]
    
    # Páginas para footer
    footer_pages = Page.objects.filter(
        is_published=True,
        show_in_menu=True
    ).filter(
        Q(published_at__isnull=True) | Q(published_at__lte=now)
    ).order_by('page_type', 'order').values(
        'id', 'title', 'slug', 'page_type'
    )
    
    # Estadísticas
    stats = {
        'total_menus': Menu.objects.filter(is_active=True).count(),
        'total_pages': Page.objects.filter(is_published=True).count(),
    }
    
    return {
        'menus': menus,
        'footer_pages': list(footer_pages),
        'stats': stats
    }