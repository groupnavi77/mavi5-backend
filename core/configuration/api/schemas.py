# core/configuration/api/schemas.py - ACTUALIZADO PARA PYDANTIC V2

from ninja import Schema
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import ConfigDict


# ============================================================================
# SCHEMAS DE SLIDER (YA EXISTENTES)
# ============================================================================

class SliderListSchema(Schema):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    section: str
    section_display: str
    image_url: Optional[str] = None
    heading: Optional[str] = None
    order: int
    is_active: bool
    is_currently_active: bool


class SliderSchema(Schema):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    section: str
    section_display: str
    image_url: Optional[str] = None
    content: Dict[str, Any]
    order: int
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SliderStatsSchema(Schema):
    model_config = ConfigDict(from_attributes=True)
    
    total: int
    active: int
    inactive: int
    scheduled: int
    by_section: Dict[str, int]


# ============================================================================
# SCHEMAS DE MENU (NUEVOS)
# ============================================================================

class MenuChildSchema(Schema):
    """Schema simplificado para hijos del menú."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    url: str
    icon: Optional[str] = None
    is_featured: bool
    has_children: bool


class MenuSchema(Schema):
    """Schema completo para un item de menú."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    url: str  # URL final calculada
    icon: Optional[str] = None
    level: int
    is_featured: bool
    has_children: bool
    children: List['MenuSchema'] = []


# Necesario para la recursión
MenuSchema.model_rebuild()


class MenuListSchema(Schema):
    """Schema simplificado para listado de menús."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    menu_type: str
    menu_type_display: str
    link_type: str
    url: str
    icon: Optional[str] = None
    order: int
    level: int
    is_active: bool
    parent_id: Optional[int] = None


class MenuTreeSchema(Schema):
    """Schema para árbol de menús."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    url: str
    icon: Optional[str] = None
    is_featured: bool
    level: int
    children: List['MenuTreeSchema'] = []


MenuTreeSchema.model_rebuild()


# ============================================================================
# SCHEMAS DE PAGE (NUEVOS)
# ============================================================================

class PageListSchema(Schema):
    """Schema simplificado para listado de páginas."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    page_type: str
    page_type_display: str
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = None
    is_published: bool
    published_at: Optional[datetime] = None
    reading_time: int


class PageDetailSchema(Schema):
    """Schema completo para detalle de página."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    page_type: str
    page_type_display: str
    template: str
    template_display: str
    content: str
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    is_published: bool
    show_in_menu: bool
    require_auth: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    reading_time: int
    absolute_url: str


class PageSEOSchema(Schema):
    """Schema solo con información SEO."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    slug: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    absolute_url: str