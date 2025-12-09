from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ==============================================================================
# 1. ESQUEMAS ANIDADOS
# ==============================================================================

class DiscountCampaignSchema(Schema):
    """Schema para campañas de descuento"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    campaign_type: str
    discount: Decimal
    discount_type: str
    start_date: datetime
    expiration_date: datetime
    is_active: bool
    priority: int

class CategorySchema(Schema):
    """Schema para categoría (asume que ya existe en tu código)"""
    id: int
    name: str
    slug: Optional[str] = None

class ImageSchema(Schema):
    """Schema para imágenes del producto"""
    id: int
    image_url: Optional[str] = None
    
    @staticmethod
    def resolve_image_url(obj):
        if obj.image:
            return obj.image.url
        return None

class PriceSchema(Schema):
    """Schema para precios con sistema de descuentos multinivel"""
    id: int
    price: Decimal
    unit: str 
    discount: Optional[Decimal] = None
    discount_type: Optional[str] = None 
    quantity: int
    time_production: Optional[int] = None
    
    # Campos calculados con el sistema de descuentos multinivel
    price_old: Optional[Decimal] = None  # Precio tachado (si hay descuento)
    price_new: Decimal  # Precio final con descuento aplicado
    percentaje_discount: Optional[int] = None  # % de descuento
    has_discount: bool = False  # ¿Tiene descuento aplicable?
    discount_source: Optional[str] = None  # "campaign", "category", "product", "price"
    discount_name: Optional[str] = None  # Nombre del descuento aplicado
    
    @staticmethod
    def resolve_price_old(obj):
        """Retorna el precio original si hay descuento"""
        return obj.price_old()
    
    @staticmethod
    def resolve_price_new(obj):
        """Retorna el precio final con descuento aplicado"""
        return obj.price_new()
    
    @staticmethod
    def resolve_percentaje_discount(obj):
        """Retorna el % de descuento"""
        return obj.percentaje_discount()
    
    @staticmethod
    def resolve_has_discount(obj):
        """Indica si tiene algún descuento"""
        return obj.has_discount()
    
    @staticmethod
    def resolve_discount_source(obj):
        """
        Indica la fuente del descuento aplicado.
        Returns: "campaign", "category", "product", "price", o None
        """
        return obj.discount_source()
    
    @staticmethod
    def resolve_discount_name(obj):
        """
        Nombre descriptivo del descuento aplicado.
        Ej: "Black Friday 2024", "Descuento en Papelería", etc.
        """
        return obj.discount_name()

class DiscountSchema(Schema):
    """Schema para descuentos"""
    id: int
    discount: Optional[Decimal] = None
    discount_type: Optional[str] = None
    start_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_active: bool = False
    
    @staticmethod
    def resolve_is_active(obj):
        """Verifica si el descuento está activo"""
        from django.utils import timezone
        now = timezone.now()
        
        if not obj.discount or obj.discount == 0:
            return False
        
        # Verificar fechas
        if obj.start_date and obj.start_date > now:
            return False
        
        if obj.expiration_date and obj.expiration_date < now:
            return False
        
        return True

# ==============================================================================
# 2. ESQUEMAS PRINCIPALES (OUTPUT)
# ==============================================================================

class ProductBaseOut(Schema):
    """Schema completo para salida de ProductBase"""
    # Metadatos
    id: int
    key: str
    created_at: datetime
    updated_at: datetime
    
    # Campos base
    title: str
    slug: str
    published: bool
    short_description: Optional[str] = None
    description: str  # HTMLField
    
    # Imagen principal
    image_url: Optional[str] = None 
    
    # Relaciones
    tags: List[str] = []
    category: CategorySchema
    images: List[ImageSchema] = []
    prices: List[PriceSchema] = []
    discounts: List[DiscountSchema] = []
    
    # Campos calculados
    price_range: Optional[dict] = None  # {'min': Decimal, 'max': Decimal}
    has_active_discount: bool = False
    
    # --- Resolutores ---
    
    @staticmethod
    def resolve_image_url(obj):
        """Resuelve la URL de la imagen principal"""
        if obj.image:
            try:
                # Si usas easy_thumbnails con aliases
                thumbnail = obj.image['img316']
                return thumbnail.url
            except:
                # Fallback a la imagen original
                return obj.image.url
        return None

    @staticmethod
    def resolve_tags(obj):
        """Resuelve los tags del producto"""
        return list(obj.tag.names())
    
    @staticmethod
    def resolve_images(obj):
        """Resuelve las imágenes adicionales"""
        return list(obj.product_base_images.all())
    
    @staticmethod
    def resolve_prices(obj):
        """Resuelve los precios ordenados por cantidad"""
        return list(obj.product_base_prices.all().order_by('quantity'))
    
    @staticmethod
    def resolve_discounts(obj):
        """Resuelve los descuentos"""
        return list(obj.product_base_discounts.all())
    
    @staticmethod
    def resolve_price_range(obj):
        """Calcula el rango de precios"""
        prices = obj.product_base_prices.all()
        if not prices:
            return None
        
        price_values = [p.price for p in prices]
        return {
            'min': min(price_values),
            'max': max(price_values)
        }
    
    @staticmethod
    def resolve_has_active_discount(obj):
        """Verifica si tiene descuentos activos"""
        from django.utils import timezone
        now = timezone.now()
        
        return obj.product_base_discounts.filter(
            discount__gt=0,
            start_date__lte=now,
            expiration_date__gte=now
        ).exists()


class ProductBaseListOut(Schema):
    """Schema simplificado para listados (menos campos para mejor performance)"""
    id: int
    key: str
    title: str
    slug: str
    short_description: Optional[str] = None
    image_url: Optional[str] = None
    tags: List[str] = []
    category_name: Optional[str] = None
    price_range: Optional[dict] = None
    has_active_discount: bool = False
    created_at: datetime
    
    @staticmethod
    def resolve_image_url(obj):
        if obj.image:
            try:
                thumbnail = obj.image['img316']
                return thumbnail.url
            except:
                return obj.image.url
        return None
    
    @staticmethod
    def resolve_tags(obj):
        return list(obj.tag.names())
    
    @staticmethod
    def resolve_category_name(obj):
        return obj.category.title if obj.category else None
    
    @staticmethod
    def resolve_price_range(obj):
        prices = obj.product_base_prices.all()
        if not prices:
            return None
        price_values = [p.price for p in prices]
        return {'min': min(price_values), 'max': max(price_values)}
    
    @staticmethod
    def resolve_has_active_discount(obj):
        from django.utils import timezone
        now = timezone.now()
        return obj.product_base_discounts.filter(
            discount__gt=0,
            start_date__lte=now,
            expiration_date__gte=now
        ).exists()