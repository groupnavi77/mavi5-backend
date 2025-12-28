
# ============================================
# SCHEMAS ACTUALIZADOS (schemas.py)
# ============================================


from ninja import Schema
from typing import Optional, Dict, Any
from datetime import datetime

class SliderListSchema(Schema):
    id: int
    title: str
    slug: str  # ✨ Agregar slug
    section: str
    section_display: str
    image_url: Optional[str] = None
    heading: Optional[str] = None
    order: int
    is_active: bool
    is_currently_active: bool


class SliderSchema(Schema):
    id: int
    title: str
    slug: str  # ✨ Agregar slug
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
    total: int
    active: int
    inactive: int
    scheduled: int
    by_section: Dict[str, int]
