from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.category.models import Category
from core.product_base.models import ProductBase

# ==============================================================================
# MODELOS DE CAMPAÑAS DE DESCUENTO
# ==============================================================================

class DiscountCampaign(models.Model):
    """
    Campañas de descuento globales (Black Friday, Cyber Monday, etc.)
    Tienen la MÁXIMA PRIORIDAD sobre todos los demás descuentos.
    """
    TYPE = (
        ('Amount', 'Monto Fijo'),
        ('Percentaje', 'Porcentaje'),
    )
    
    CAMPAIGN_TYPE = (
        ('global', 'Global - Todos los productos'),
        ('category', 'Por Categoría'),
        ('products', 'Productos Específicos'),
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Nombre de la campaña (ej: Black Friday 2024)"
    )
    code = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Código único (ej: black-friday-2024)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción de la campaña"
    )
    
    # Tipo de campaña
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPE,
        default='global',
        help_text="Alcance de la campaña"
    )
    
    # Descuento
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        help_text="Valor del descuento"
    )
    discount_type = models.CharField(
        max_length=10,
        choices=TYPE,
        default='Percentaje'
    )
    
    # Fechas
    start_date = models.DateTimeField(
        help_text="Inicio de la campaña"
    )
    expiration_date = models.DateTimeField(
        help_text="Fin de la campaña"
    )
    
    # Relaciones (para campañas específicas)
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='discount_campaigns',
        help_text="Categorías incluidas (solo si campaign_type='category')"
    )
    products = models.ManyToManyField(
        ProductBase,
        blank=True,
        related_name='discount_campaigns',
        help_text="Productos incluidos (solo si campaign_type='products')"
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        help_text="¿Campaña activa?"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Prioridad (mayor número = mayor prioridad)"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-start_date']
        verbose_name = 'Campaña de Descuento'
        verbose_name_plural = 'Campañas de Descuento'
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'expiration_date']),
            models.Index(fields=['-priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.discount}{self.get_discount_type_display()})"
    
    def is_currently_active(self):
        """Verifica si la campaña está activa en este momento"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.expiration_date
        )
    
    def applies_to_product(self, product):
        """Verifica si la campaña aplica a un producto específico"""
        if not self.is_currently_active():
            return False
        
        if self.campaign_type == 'global':
            return True
        elif self.campaign_type == 'category':
            return self.categories.filter(id=product.category_id).exists()
        elif self.campaign_type == 'products':
            return self.products.filter(id=product.id).exists()
        
        return False
    
    def calculate_discount(self, price):
        """Calcula el monto de descuento para un precio dado"""
        if self.discount_type == 'Percentaje':
            return price * (self.discount / 100)
        else:
            return min(self.discount, price)  # No puede ser mayor que el precio


class CategoryDiscount(models.Model):
    """
    Descuentos específicos por categoría.
    Prioridad MEDIA-ALTA (después de campañas globales).
    """
    TYPE = (
        ('Amount', 'Monto Fijo'),
        ('Percentaje', 'Porcentaje'),
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_discounts'
    )
    name = models.CharField(
        max_length=255,
        help_text="Nombre del descuento"
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        help_text="Valor del descuento"
    )
    discount_type = models.CharField(
        max_length=10,
        choices=TYPE,
        default='Percentaje'
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Inicio del descuento (opcional)"
    )
    expiration_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fin del descuento (opcional)"
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Descuento por Categoría'
        verbose_name_plural = 'Descuentos por Categoría'
    
    def __str__(self):
        return f"{self.category.title} - {self.discount}{self.get_discount_type_display()}"
    
    def is_currently_active(self):
        """Verifica si el descuento está activo"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.start_date and self.start_date > now:
            return False
        
        if self.expiration_date and self.expiration_date < now:
            return False
        
        return True


# ==============================================================================
# MANAGER CENTRALIZADO DE DESCUENTOS
# ==============================================================================

class DiscountManager:
    """
    Manager centralizado para calcular descuentos con jerarquía de prioridad.
    
    Jerarquía:
    1. Campaña Global/Específica (DiscountCampaign)
    2. Descuento por Categoría (CategoryDiscount)
    3. Descuento de Producto (Discount)
    4. Descuento de Precio (Price.discount)
    """
    
    @staticmethod
    def get_best_discount_for_price(price_obj):
        """
        Calcula el mejor descuento aplicable a un objeto Price.
        
        Args:
            price_obj: Instancia de Price
            
        Returns:
            dict: {
                'discount_amount': Decimal,
                'discount_percentage': int,
                'discount_source': str,
                'discount_name': str,
                'has_discount': bool
            }
        """
        product = price_obj.product
        original_price = price_obj.price
        
        # 1. Verificar Campaña Global/Específica (MÁXIMA PRIORIDAD)
        active_campaign = DiscountCampaign.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            expiration_date__gte=timezone.now()
        ).order_by('-priority').first()
        
        if active_campaign and active_campaign.applies_to_product(product):
            discount_amount = active_campaign.calculate_discount(original_price)
            return {
                'discount_amount': discount_amount,
                'discount_percentage': round((discount_amount / original_price) * 100),
                'discount_source': 'campaign',
                'discount_name': active_campaign.name,
                'has_discount': True,
                'discount_object': active_campaign
            }
        
        # 2. Verificar Descuento por Categoría
        category_discount = CategoryDiscount.objects.filter(
            category=product.category,
            is_active=True
        ).first()
        
        if category_discount and category_discount.is_currently_active():
            if category_discount.discount_type == 'Percentaje':
                discount_amount = original_price * (category_discount.discount / 100)
            else:
                discount_amount = min(category_discount.discount, original_price)
            
            return {
                'discount_amount': discount_amount,
                'discount_percentage': round((discount_amount / original_price) * 100),
                'discount_source': 'category',
                'discount_name': f"Descuento en {product.category.title}",
                'has_discount': True,
                'discount_object': category_discount
            }
        
        # 3. Verificar Descuento de Producto (Discount model)
        product_discount = product.product_base_discounts.filter(
            discount__gt=0
        ).first()
        
        if product_discount:
            now = timezone.now()
            # Verificar fechas si existen
            if product_discount.start_date or product_discount.expiration_date:
                if product_discount.start_date and product_discount.start_date > now:
                    product_discount = None
                elif product_discount.expiration_date and product_discount.expiration_date < now:
                    product_discount = None
            
            if product_discount:
                if product_discount.discount_type == 'Percentaje':
                    discount_amount = original_price * (product_discount.discount / 100)
                else:
                    discount_amount = min(product_discount.discount, original_price)
                
                return {
                    'discount_amount': discount_amount,
                    'discount_percentage': round((discount_amount / original_price) * 100),
                    'discount_source': 'product',
                    'discount_name': f"Descuento en {product.title}",
                    'has_discount': True,
                    'discount_object': product_discount
                }
        
        # 4. Verificar Descuento del Precio individual
        if price_obj.discount:
            if price_obj.discount_type == 'Percentaje':
                discount_amount = original_price * (price_obj.discount / 100)
            else:
                discount_amount = min(price_obj.discount, original_price)
            
            return {
                'discount_amount': discount_amount,
                'discount_percentage': round((discount_amount / original_price) * 100),
                'discount_source': 'price',
                'discount_name': f"Descuento por cantidad ({price_obj.quantity}+)",
                'has_discount': True,
                'discount_object': price_obj
            }
        
        # 5. Sin descuento
        return {
            'discount_amount': Decimal('0.00'),
            'discount_percentage': 0,
            'discount_source': None,
            'discount_name': None,
            'has_discount': False,
            'discount_object': None
        }