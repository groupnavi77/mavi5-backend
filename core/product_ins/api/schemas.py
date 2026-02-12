from ninja import Schema
from typing import Optional, List
from datetime import datetime

# --- Image Schema ---
class ImageSchema(Schema):
    id: int
    image_url: Optional[str] = None
    
    @staticmethod
    def resolve_image_url(obj):
        if obj.image:
                        # Llama al alias definido en settings
            thumbnail = obj.image['img316'] 
            return thumbnail.url
        return None


# --- Product OUT Schema ---
class ProductOut(Schema):
    # Metadatos y Claves
    id: int
    key: str
    created_at: datetime
    updated_at: datetime
    
    # Campos base
    description: Optional[str] = None
    published: bool
    
    # Imagen principal
    image_url: Optional[str] = None
    
    # Galería de imágenes adicionales
    images: List[ImageSchema] = []
    
    # Tags
    tags: List[str] = []
    
    # Información del producto base (nombre, precio, etc.)
    product_base_name: Optional[str] = None
    product_base_slug: Optional[str] = None
    product_base_key: Optional[str] = None
    
    # Usuario creador
    user_name: Optional[str] = None
    
    @staticmethod
    def resolve_image_url(obj):
        """Resuelve la URL de la imagen principal"""
        if obj.image:
            # Llama al alias definido en settings
            thumbnail = obj.image['img316'] 
            return thumbnail.url
        return None
    
    @staticmethod
    def resolve_images(obj):
        """Resuelve las imágenes adicionales"""
        return list(obj.product_images.all())
    
    @staticmethod
    def resolve_tags(obj):
        """Resuelve los tags del producto"""
        return [tag.name for tag in obj.tag.all()]
    
    @staticmethod
    def resolve_product_base_name(obj):
        """Resuelve el nombre del ProductBase"""
        return obj.Product_base.title if obj.Product_base else None
    
    @staticmethod
    def resolve_product_base_slug(obj):
        """Resuelve el slug del ProductBase"""
        return obj.Product_base.slug if obj.Product_base else None
    
    @staticmethod
    def resolve_product_base_key(obj):
        """Resuelve la key del ProductBase"""
        return obj.Product_base.key if obj.Product_base else None
    
    @staticmethod
    def resolve_user_name(obj):
        """Resuelve el nombre del usuario"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return None


# --- Product Detail Schema (con más información) ---
class ProductDetailOut(ProductOut):
    """Schema extendido para el detalle del producto"""
    pass  # Puedes agregar campos adicionales aquí si lo necesitas