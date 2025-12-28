from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ==============================================================================
# 1. ESQUEMAS ANIDADOS
# ==============================================================================


class CategorySchema(Schema):
    """Schema para categoría (asume que ya existe en tu código)"""
    id: int
    title: str
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
    def resolve_image_url(obj, context): 
        # Si no hay imagen, salimos.
        if not obj.image:
            return None
            
        image_url = obj.image.url
        
        # 1. Chequeo de URL Absoluta (Producción S3)
        # Si la URL ya comienza con http/s, es S3. La devolvemos directamente.
        if image_url.startswith('http') or image_url.startswith('https'):
            return image_url
            
        # 2. Convertir Relativa a Absoluta (Desarrollo)
        # Si la URL es relativa y tenemos el objeto request (que debe estar
        # presente gracias a @paginate y la firma del endpoint).
        request = context.get('request')

        if request:
            # Esta es la magia que hace DRF: convierte /media/... a http://host:port/media/...
            return request.build_absolute_uri(image_url)
                
        # 3. Fallback: Devolver la URL relativa (Solo si falla el request, lo cual es raro)
        return image_url

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
        """
        Calcula el rango de precios con información completa de descuentos.
        Incluye: nombre de campaña, fecha de expiración, ahorro en monto.
        """
        prices = obj.product_base_prices.all()
        if not prices:
            return None
        
        # Precios originales
        price_values = [p.price for p in prices]
        min_price = min(price_values)
        max_price = max(price_values)

        # Encontrar cantidad y unidad del precio mínimo
        min_cantity = 0
        min_unit = None
        max_cantity = 0
        max_unit = None
        

        for p in prices:
            if p.price == min_price:
                min_cantity = p.quantity
                min_unit = p.unit
                min_unit_smart = p.get_unit_display_smart()
            if p.price == max_price:
                max_cantity = p.quantity
                max_unit = p.unit
                max_unit_smart = p.get_unit_display_smart()

        
        # Precios con descuento
        price_new_values = [p.price_new() for p in prices]
        min_discounted = min(price_new_values)
        max_discounted = max(price_new_values)
        
        # Verificar si hay descuentos
        has_discount = any(p.has_discount() for p in prices)
        
        # Inicializar variables
        campaign_name = None
        discount_expires_at = None
        discount_info_extra = {}
        
        if has_discount:
            # Calcular descuentos y ahorros
            discount_percentages = [
                p.percentaje_discount() for p in prices 
                if p.percentaje_discount() is not None
            ]
            
            # Calcular ahorro en monto
            savings_list = [
                p.price - p.price_new() for p in prices 
                if p.has_discount()
            ]
            
            if discount_percentages:
                max_discount = max(discount_percentages)
                min_discount = min(discount_percentages)
                discount_info_extra.update({
                    'max_discount_percentage': max_discount,
                    'min_discount_percentage': min_discount
                })
            
            if savings_list:
                max_savings = max(savings_list)
                min_savings = min(savings_list)
                discount_info_extra.update({
                    'max_savings': str(max_savings),
                    'min_savings': str(min_savings)
                })
            
            # Obtener información de campaña
            first_price_with_discount = next(
                (p for p in prices if p.has_discount()), 
                None
            )
            
            if first_price_with_discount:
                discount_data = first_price_with_discount.get_discount_info()
                campaign_name = discount_data.get('discount_name')
                
                discount_obj = discount_data.get('discount_object')
                if discount_obj and hasattr(discount_obj, 'expiration_date'):
                    discount_expires_at = discount_obj.expiration_date
        
        result = {
            'min': str(min_price),
            'max': str(max_price),
            'min_cantity': min_cantity,
            'min_unit': min_unit,
            'min_unit_smart': min_unit_smart,
            'max_cantity': max_cantity,
            'max_unit': max_unit,
            'max_unit_smart': max_unit_smart,
            'min_discounted': str(min_discounted),
            'max_discounted': str(max_discounted),
            'has_discount': has_discount,
        }
        
        if has_discount:
            result.update({
                **discount_info_extra,
                'campaign_name': campaign_name,
                'discount_expires_at': discount_expires_at.isoformat() if discount_expires_at else None
            })
        
        return result
    
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
    
    # Rango de precios CON y SIN descuentos
    price_range: Optional[dict] = None
    
    has_active_discount: bool = False
    created_at: datetime
    
    @staticmethod
    def resolve_image_url(obj, context):
        """Resuelve la URL absoluta de la imagen o thumbnail."""
        
        if not obj.image:
            return None
        
        try:
            # 1. Obtener la URL (Intenta obtener el thumbnail)
            thumbnail = obj.image['img316']
            url = thumbnail.url
        except:
            # Fallback a la imagen original
            url = obj.image.url
        
        # 2. Lógica para convertir a URL Absoluta
        
        # Si la URL ya es absoluta (ej: S3), la devolvemos sin modificar
        if url.startswith('http') or url.startswith('https'):
            return url
            
        # Si la URL es relativa (ej: /media/cache/...) y tenemos el request
        request = context.get('request')

        if request:
            # Esto convierte /media/... a http://localhost:8000/media/... en desarrollo
            return request.build_absolute_uri(url)
                
        # Fallback de seguridad (devuelve la URL relativa si no hay request)
        return url
    
    @staticmethod
    def resolve_tags(obj):
        return list(obj.tag.names())
    
    @staticmethod
    def resolve_category_name(obj):
        return obj.category.title if obj.category else None
    
    @staticmethod
    def resolve_price_range(obj):
        """
        Calcula el rango de precios original Y con descuentos aplicados.
        
        Returns:
            {
                "min": "10.00",                    # Precio mínimo original
                "max": "50.00",                    # Precio máximo original
                "min_cantity": 100,                # Cantidad de pedido del precio mínimo
                "min_unit": "unidad",              # Unidad de medida del precio mínimo
                "max_cantity": 1000,               # Cantidad de pedido del precio máximo
                "max_unit": "unidad",              # Unidad de medida del precio máximo
                "min_discounted": "8.00",          # Precio mínimo con descuento
                "max_discounted": "40.00",         # Precio máximo con descuento
                "has_discount": true,              # ¿Hay algún descuento?
                "max_discount_percentage": 20,     # Mayor % de descuento
                "max_savings": "25.00",            # Ahorro máximo en monto
                "min_savings": "2.00",             # Ahorro mínimo en monto
                "campaign_name": "Black Friday",   # Nombre de la campaña activa
                "discount_expires_at": "2024-11-29T23:59:59Z"  # Cuándo expira
            }
        """
        prices = obj.product_base_prices.all()
        if not prices:
            return None
        
        # Calcular precios originales
        price_values = [p.price for p in prices]
        min_price = min(price_values)
        max_price = max(price_values)
        
        # Encontrar cantidad y unidad del precio mínimo
        min_cantity = 0
        min_unit = None
        max_cantity = 0
        max_unit = None
        

        for p in prices:
            if p.price == min_price:
                min_cantity = p.quantity
                min_unit = p.unit
                min_unit_smart = p.get_unit_display_smart()
            if p.price == max_price:
                max_cantity = p.quantity
                max_unit = p.unit
                max_unit_smart = p.get_unit_display_smart()



        # Calcular precios con descuento
        price_new_values = [p.price_new() for p in prices]
        min_discounted = min(price_new_values)
        max_discounted = max(price_new_values)
        
        # Calcular si hay descuento
        has_discount = any(p.has_discount() for p in prices)
        
        # Inicializar variables de campaña
        campaign_name = None
        discount_expires_at = None
        max_discount_percentage = 0
        max_savings = Decimal('0.00')
        min_savings = Decimal('0.00')
        
        if has_discount:
            # Calcular el mayor porcentaje de descuento
            discount_percentages = [
                p.percentaje_discount() for p in prices 
                if p.percentaje_discount() is not None
            ]
            if discount_percentages:
                max_discount_percentage = max(discount_percentages)
            
            # Calcular ahorro en monto
            savings_list = [
                p.price - p.price_new() for p in prices 
                if p.has_discount()
            ]
            if savings_list:
                max_savings = max(savings_list)
                min_savings = min(savings_list)
            
            # Obtener información de la campaña activa
            # Usamos el primer precio para obtener info de descuento
            first_price_with_discount = next(
                (p for p in prices if p.has_discount()), 
                None
            )
            
            if first_price_with_discount:
                discount_info = first_price_with_discount.get_discount_info()
                
                # Nombre de la campaña/descuento
                campaign_name = discount_info.get('discount_name')
                
                # Fecha de expiración según la fuente del descuento
                discount_obj = discount_info.get('discount_object')
                if discount_obj:
                    # Si es una campaña
                    if hasattr(discount_obj, 'expiration_date'):
                        discount_expires_at = discount_obj.expiration_date
                    # Si es un descuento de categoría con fecha
                    elif hasattr(discount_obj, 'expiration_date') and discount_obj.expiration_date:
                        discount_expires_at = discount_obj.expiration_date
        
        result = {
            'min': str(min_price),
            'max': str(max_price),
            'min_cantity': min_cantity,
            'min_unit': min_unit,
            'min_unit_smart': min_unit_smart,
            'max_cantity': max_cantity,
            'max_unit': max_unit,
            'max_unit_smart': max_unit_smart,
            'min_discounted': str(min_discounted),
            'max_discounted': str(max_discounted),
            'has_discount': has_discount,
        }
        
        # Agregar información adicional solo si hay descuento
        if has_discount:
            result.update({
                'max_discount_percentage': max_discount_percentage,
                'max_savings': str(max_savings),
                'min_savings': str(min_savings),
                'campaign_name': campaign_name,
                'discount_expires_at': discount_expires_at.isoformat() if discount_expires_at else None
            })
        
        return result
    
    @staticmethod
    def resolve_has_active_discount(obj):
        from django.utils import timezone
        now = timezone.now()
        
        # Verificar si hay campaña activa que aplique
        from core.campaing.models import DiscountCampaign
        active_campaign = DiscountCampaign.objects.filter(
            is_active=True,
            start_date__lte=now,
            expiration_date__gte=now
        ).first()
        
        if active_campaign and active_campaign.applies_to_product(obj):
            return True
        
        # Verificar descuentos en los precios
        return obj.product_base_prices.filter(
            discount__gt=0
        ).exists() or obj.product_base_discounts.filter(
            discount__gt=0
        ).exists()