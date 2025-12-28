from django.db import models
import random

from tinymce.models import HTMLField
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager

from core.category.models import Category


def saveSystemCode(inClass, inCode, inPK, prefix):
    """Genera un código único para el producto"""
    key = inCode
    if not key:
        key = str(random.randint(10000000000, 99999999999))

    while inClass.objects.filter(key=key).exclude(pk=inPK).exists():
        key = str(random.randint(10000000000, 99999999999))

    return key


class ProductBase(models.Model):
    """
    Producto Base: Plantilla de productos (ej: "Tarjetas de Presentación").
    Los usuarios crean instancias personalizadas de estos productos.
    """
    key = models.CharField(
        max_length=25, 
        blank=True, 
        null=True, 
        unique=True,
        db_index=True,
        help_text="Código único del producto base"
    )
    title = models.CharField(
        max_length=255,
        help_text="Nombre del producto (ej: Tarjetas de Presentación)"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="URL amigable (ej: tarjetas-de-presentacion)"
    )
    short_description = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Descripción breve para listados"
    )
    description = HTMLField(
        help_text="Descripción completa con formato HTML"
    )
    image = ThumbnailerImageField(
        upload_to='images/product-base',
        blank=True,
        max_length=255,
        resize_source=dict(size=(1300, 0), crop=True),
        help_text="Imagen principal del producto"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',  # Más simple
        help_text="Categoría del producto"
    )
    tag = TaggableManager(
        verbose_name="Tags",
        help_text="Tags de estilo y categoría (ej: #Económico, #Packaging)",
        blank=True
    )
    published = models.BooleanField(
        default=True,
        db_index=True,
        help_text="¿Visible para los usuarios?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto Base'
        verbose_name_plural = 'Productos Base'
        indexes = [
            models.Index(fields=['-created_at', 'published']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'published']),
        ]

    def save(self, *args, **kwargs):
        self.key = saveSystemCode(ProductBase, self.key, self.pk, 'pb_')
        super(ProductBase, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class ImageProductBase(models.Model):
    """Galería de imágenes adicionales para un ProductBase"""
    product = models.ForeignKey(
        ProductBase,
        on_delete=models.CASCADE,
        related_name='product_base_images'
    )
    image = ThumbnailerImageField(
        upload_to='images/product-base/gallery',
        max_length=255,
        resize_source=dict(size=(0, 1300), crop=True)
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Imagen de producto base'
        verbose_name_plural = 'Imágenes de productos base'

    def __str__(self):
        return f"Imagen de {self.product.title}"


class Price(models.Model):
    """
    Tabla de precios por cantidad.
    Ejemplo: 100 unidades = $10, 500 unidades = $8, etc.
    """
    TYPE = (
        ('Amount', 'Monto Fijo'),
        ('Percentaje', 'Porcentaje'),
    )

    UNIT = (
        ('Unidad', 'Unidad'),
        ('Docena', 'Docena'),
        ('Caja', 'Caja'),
        ('Paquete', 'Paquete'),
        ('Kilogramo', 'Kilogramo'),
        ('Metro', 'Metro'),
        ('Litro', 'Litro'),
    )
    
    # Mapeo de singular a plural
    UNIT_PLURAL = {
        'Unidad': 'Unidades',
        'Docena': 'Docenas',
        'Caja': 'Cajas',
        'Paquete': 'Paquetes',
        'Kilogramo': 'Kilogramos',
        'Metro': 'Metros',
        'Litro': 'Litros',
    }
    
    product = models.ForeignKey(
        ProductBase,
        on_delete=models.CASCADE,
        related_name='product_base_prices'
    )
    price = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        help_text="Precio base por unidad/docena"
    )
    unit = models.CharField(
        max_length=225,
        choices=UNIT,
        help_text="Unidad de medida"
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        blank=True,
        null=True,
        help_text="Descuento aplicable a este precio específico"
    )
    discount_type = models.CharField(
        max_length=10,
        choices=TYPE,
        default='Amount',
        blank=True,
        null=True
    )
    quantity = models.IntegerField(
        help_text="Cantidad mínima para este precio"
    )
    time_production = models.IntegerField(
        default=1,
        null=True,
        help_text="Días de producción estimados"
    )

    class Meta:
        ordering = ['quantity']  # Ordenar por cantidad ascendente
        verbose_name = 'Precio'
        verbose_name_plural = 'Precios'
        indexes = [
            models.Index(fields=['product', 'quantity']),
        ]

    def __str__(self):
        return f"{self.product.title} - {self.quantity} {self.unit}: ${self.price}"
    
    def get_unit_display_smart(self):
        """
        Retorna la unidad en singular o plural según la cantidad.
        
        Ejemplos:
        - quantity=1, unit='Unidad' → 'Unidad'
        - quantity=2, unit='Unidad' → 'Unidades'
        - quantity=1, unit='Docena' → 'Docena'
        - quantity=5, unit='Docena' → 'Docenas'
        """
        if self.quantity == 1:
            return self.unit  # Singular
        else:
            return self.UNIT_PLURAL.get(self.unit, self.unit + 's')  # Plural
    
    def get_unit_label(self):
        """
        Alias de get_unit_display_smart() para usar en templates.
        """
        return self.get_unit_display_smart()
    
    def get_formatted_quantity(self):
        """
        Retorna la cantidad con su unidad en formato legible.
        
        Ejemplos:
        - "1 Unidad"
        - "100 Unidades"
        - "1 Docena"
        - "5 Docenas"
        """
        return f"{self.quantity} {self.get_unit_display_smart()}"
    
    def get_price_description(self):
        """
        Retorna descripción completa del precio.
        
        Ejemplos:
        - "100 Unidades por $10.00"
        - "1 Docena por $25.50"
        """
        return f"{self.get_formatted_quantity()} por ${self.price}"
    
    def get_discount_info(self):
        """
        Obtiene información completa del descuento aplicable.
        Usa el DiscountManager para calcular con jerarquía.
        """
        from core.campaing.models import DiscountManager
        return DiscountManager.get_best_discount_for_price(self)
    
    def percentaje_discount(self):
        """
        Calcula el porcentaje de descuento aplicable.
        Usa el sistema de jerarquía multinivel.
        """
        discount_info = self.get_discount_info()
        return discount_info['discount_percentage'] if discount_info['has_discount'] else None
    
    def price_new(self):
        """
        Calcula el precio final con descuento aplicado.
        Usa el sistema de jerarquía multinivel.
        """
        discount_info = self.get_discount_info()
        return self.price - discount_info['discount_amount']
    
    def price_old(self):
        """
        Retorna el precio original si hay algún descuento aplicado.
        """
        discount_info = self.get_discount_info()
        return self.price if discount_info['has_discount'] else None
    
    def has_discount(self):
        """
        Verifica si el precio tiene algún descuento aplicable.
        """
        discount_info = self.get_discount_info()
        return discount_info['has_discount']
    
    def discount_source(self):
        """
        Retorna la fuente del descuento: 'campaign', 'category', 'product', 'price', o None
        """
        discount_info = self.get_discount_info()
        return discount_info['discount_source']
    
    def discount_name(self):
        """
        Retorna el nombre descriptivo del descuento aplicado.
        """
        discount_info = self.get_discount_info()
        return discount_info['discount_name']


class Discount(models.Model):
    """
    Descuentos temporales aplicables a un ProductBase.
    Ejemplo: 20% de descuento del 1 al 15 de diciembre.
    """
    TYPE = (
        ('Amount', 'Monto Fijo'),
        ('Percentaje', 'Porcentaje'),
    )
    
    product = models.ForeignKey(
        ProductBase,
        on_delete=models.CASCADE,
        related_name='product_base_discounts'
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        blank=True,
        null=True,
        help_text="Valor del descuento"
    )
    discount_type = models.CharField(
        max_length=10,
        choices=TYPE,
        default='Amount',
        blank=True,
        null=True
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Inicio de la promoción"
    )
    expiration_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fin de la promoción"
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'
        indexes = [
            models.Index(fields=['product', 'start_date', 'expiration_date']),
        ]

    def __str__(self):
        return f"{self.product.title} - {self.discount}% descuento"
    
    def is_active(self):
        """Verifica si el descuento está activo actualmente"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.discount or self.discount == 0:
            return False
        
        if self.start_date and self.start_date > now:
            return False
        
        if self.expiration_date and self.expiration_date < now:
            return False
        
        return True