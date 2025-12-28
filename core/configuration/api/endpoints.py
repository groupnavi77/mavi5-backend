# ============================================
# api.py - API con búsqueda por SLUG agregada
# ============================================

from ninja import Router, Query
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from ..models import Slider
from ..api.schemas import SliderSchema, SliderListSchema, SliderStatsSchema
from typing import List, Optional, Dict

router = Router()

# ============================================
# ENDPOINTS
# ============================================

# 1. LISTAR TODOS CON FILTROS Y PAGINACIÓN
@router.get("/sliders/list", response=List[SliderListSchema])
def list_sliders(
    request,
    section: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = 'order',
    currently_active_only: Optional[bool] = False
):
    """
    Lista todos los sliders con filtros
    
    Parámetros:
    - section: Filtrar por sección (ej: home_hero, home_deals)
    - is_active: true/false para filtrar por estado
    - search: Buscar en título, slug o contenido
    - order_by: Campo para ordenar (order, -order, created_at, -created_at, title)
    - currently_active_only: Solo sliders activos actualmente (considera fechas)
    
    Ejemplos:
    GET /api/sliders/list
    GET /api/sliders/list?section=home_hero
    GET /api/sliders/list?is_active=true
    GET /api/sliders/list?search=ofertas
    GET /api/sliders/list?order_by=-created_at
    GET /api/sliders/list?currently_active_only=true
    """
    
    queryset = Slider.objects.all()
    
    # Filtrar por sección
    if section:
        queryset = queryset.filter(section=section)
    
    # Filtrar por estado activo
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    # Filtrar por búsqueda en título, slug o contenido
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(slug__icontains=search) |  # ✨ Búsqueda por slug
            Q(content__icontains=search)
        )
    
    # Filtrar solo los actualmente activos (con fechas)
    if currently_active_only:
        now = timezone.now()
        queryset = queryset.filter(
            is_active=True
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
    
    # Ordenar
    valid_order_fields = ['order', '-order', 'created_at', '-created_at', 'title', '-title', 'section', 'slug', '-slug']
    if order_by in valid_order_fields:
        queryset = queryset.order_by(order_by)
    else:
        queryset = queryset.order_by('section', 'order')
    
    # Construir response
    result = []
    for slider in queryset:
        result.append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,  # ✨ Incluir slug
            'section': slider.section,
            'section_display': slider.get_section_display(),
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'heading': slider.get_content_field('heading'),
            'order': slider.order,
            'is_active': slider.is_active,
            'is_currently_active': slider.is_currently_active(),
        })
    
    return result


# 2. LISTAR POR SECCIÓN (SIN PAGINACIÓN)
@router.get("/sliders/section/{section_name}", response=List[SliderSchema])
def get_sliders_by_section(request, section_name: str, include_inactive: bool = False):
    """
    Obtiene sliders de una sección específica (solo activos por defecto)
    
    Parámetros:
    - section_name: Nombre de la sección
    - include_inactive: true para incluir inactivos
    
    Ejemplos:
    GET /api/sliders/section/home_hero
    GET /api/sliders/section/home_deals?include_inactive=true
    """
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
    
    result = []
    for slider in queryset:
        result.append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,  # ✨ Incluir slug
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


# 3. OBTENER SLIDER POR ID
@router.get("/sliders/{slider_id}", response=SliderSchema)
def get_slider(request, slider_id: int):
    """
    Obtiene un slider específico por ID
    
    Ejemplo:
    GET /api/sliders/123
    """
    try:
        slider = Slider.objects.get(id=slider_id)
        
        return {
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,  # ✨ Incluir slug
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
    except Slider.DoesNotExist:
        return {"error": "Slider no encontrado"}, 404


# 4. ✨ NUEVO: OBTENER SLIDER POR SLUG
@router.get("/sliders/slug/{slug}", response=SliderSchema)
def get_slider_by_slug(request, slug: str):
    """
    Obtiene un slider específico por SLUG (URL amigable)
    
    Parámetros:
    - slug: Slug único del slider
    
    Ejemplos:
    GET /api/sliders/slug/new-season-womens-style
    GET /api/sliders/slug/summer-sale-2024
    GET /api/sliders/slug/ofertas-navidad
    
    Response:
    {
        "id": 1,
        "title": "New Season Women's Style",
        "slug": "new-season-womens-style",
        "section": "home_hero",
        "image_url": "http://...",
        "content": {...},
        ...
    }
    """
    try:
        slider = Slider.objects.get(slug=slug)
        
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
    except Slider.DoesNotExist:
        return {"error": f"Slider con slug '{slug}' no encontrado"}, 404


# 5. ESTADÍSTICAS
@router.get("/sliders/stats/overview", response=SliderStatsSchema)
def get_slider_stats(request):
    """
    Obtiene estadísticas generales de sliders
    
    Ejemplo:
    GET /api/sliders/stats/overview
    
    Response:
    {
        "total": 15,
        "active": 10,
        "inactive": 5,
        "scheduled": 2,
        "by_section": {
            "home_hero": 3,
            "home_deals": 5
        }
    }
    """
    now = timezone.now()
    
    total = Slider.objects.count()
    active = Slider.objects.filter(is_active=True).count()
    inactive = Slider.objects.filter(is_active=False).count()
    
    # Contar programados (activos pero fuera de fecha)
    scheduled = Slider.objects.filter(
        is_active=True
    ).filter(
        Q(start_date__gt=now) | Q(end_date__lt=now)
    ).count()
    
    # Contar por sección
    by_section = {}
    sections = Slider.objects.values_list('section', flat=True).distinct()
    for section in sections:
        count = Slider.objects.filter(section=section).count()
        by_section[section] = count
    
    return {
        'total': total,
        'active': active,
        'inactive': inactive,
        'scheduled': scheduled,
        'by_section': by_section
    }


# 6. SECCIONES DISPONIBLES
@router.get("/sliders/sections/list", response=List[dict])
def list_sections(request):
    """
    Lista todas las secciones disponibles con conteo
    
    Ejemplo:
    GET /api/sliders/sections/list
    
    Response:
    [
        {
            "value": "home_hero",
            "label": "Home - Hero Banner",
            "count": 5,
            "active_count": 3
        }
    ]
    """
    sections_data = []
    
    for section_value, section_label in Slider.SECTION_CHOICES:
        total_count = Slider.objects.filter(section=section_value).count()
        active_count = Slider.objects.filter(
            section=section_value, 
            is_active=True
        ).count()
        
        if total_count > 0:  # Solo mostrar secciones con sliders
            sections_data.append({
                'value': section_value,
                'label': section_label,
                'count': total_count,
                'active_count': active_count
            })
    
    return sections_data


# 7. ✨ BÚSQUEDA RÁPIDA (ahora incluye slug)
@router.get("/sliders/search", response=List[SliderListSchema])
def search_sliders(request, q: str, limit: int = 10):
    """
    Búsqueda rápida de sliders en título, slug y contenido
    
    Parámetros:
    - q: Término de búsqueda
    - limit: Número máximo de resultados (default: 10)
    
    Ejemplos:
    GET /api/sliders/search?q=ofertas
    GET /api/sliders/search?q=womens-style
    GET /api/sliders/search?q=navidad&limit=5
    """
    
    queryset = Slider.objects.filter(
        Q(title__icontains=q) |
        Q(slug__icontains=q) |  # ✨ Incluir slug en búsqueda
        Q(content__icontains=q) |
        Q(section__icontains=q)
    ).order_by('-is_active', 'order')[:limit]
    
    result = []
    for slider in queryset:
        result.append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,  # ✨ Incluir slug
            'section': slider.section,
            'section_display': slider.get_section_display(),
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'heading': slider.get_content_field('heading'),
            'order': slider.order,
            'is_active': slider.is_active,
            'is_currently_active': slider.is_currently_active(),
        })
    
    return result


# 8. SLIDERS ACTIVOS AGRUPADOS POR SECCIÓN
@router.get("/sliders/active/by-section", response=Dict[str, List[SliderListSchema]])
def get_active_by_section(request):
    """
    Obtiene todos los sliders activos agrupados por sección
    
    Ejemplo:
    GET /api/sliders/active/by-section
    
    Response:
    {
        "home_hero": [...],
        "home_deals": [...]
    }
    """
    now = timezone.now()
    
    sliders = Slider.objects.filter(
        is_active=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('section', 'order')
    
    # Agrupar por sección
    result = {}
    for slider in sliders:
        section = slider.section
        if section not in result:
            result[section] = []
        
        result[section].append({
            'id': slider.id,
            'title': slider.title,
            'slug': slider.slug,  # ✨ Incluir slug
            'section': slider.section,
            'section_display': slider.get_section_display(),
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'heading': slider.get_content_field('heading'),
            'order': slider.order,
            'is_active': slider.is_active,
            'is_currently_active': slider.is_currently_active(),
        })
    
    return result

