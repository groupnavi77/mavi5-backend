from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Category (MPTTModel) ---
class CategorySchema(Schema):
    id: int
    title: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    
    # Resolver la URL de la imagen de categoría si existe
    @staticmethod
    def resolve_cat_image_url(obj):
        if obj.cat_image:
            return obj.cat_image.url
        return None