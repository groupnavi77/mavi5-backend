from django.db import models
import random

from tinymce.models import HTMLField
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager

from core.product_base.models import ProductBase
from core.user.models import UserAccount


def saveSystemCode(inClass, inCode, inPK, prefix):
    """Genera un código único para el producto"""
    key = inCode
    if not key:
        key = str(random.randint(10000000000, 99999999999))

    while inClass.objects.filter(key=key).exclude(pk=inPK).exists():
        key = str(random.randint(10000000000, 99999999999))

    return key


class Product(models.Model):
    """
    Modelo de Producto personalizado (instancia de un ProductBase).
    Similar a un "diseño" o "variación" personalizada en Vistaprint.
    """
    key = models.CharField(
        max_length=25, 
        blank=True, 
        null=True, 
        unique=True,
        db_index=True,  # Índice para búsquedas rápidas
        help_text="Código único del producto"
    )
    image = ThumbnailerImageField(
        upload_to='images/products', 
        blank=True, 
        max_length=255, 
        resize_source=dict(size=(1300, 0), crop=True),
        help_text="Imagen principal del producto"
    )
    description = models.TextField(
        max_length=1000, 
        blank=True,
        help_text="Descripción del producto personalizado"
    )
    Product_base = models.ForeignKey(
        ProductBase, 
        on_delete=models.CASCADE, 
        related_name='product_instances',  # Mejor nombre semántico
        help_text="Producto base del cual deriva esta instancia"
    )
    user = models.ForeignKey(
        UserAccount, 
        on_delete=models.CASCADE, 
        related_name='products',  # Más simple y directo
        help_text="Usuario creador del producto"
    )
    tag = TaggableManager(
        verbose_name="Tags", 
        help_text="Tags de estilo y categoría (ej: #Económico, #Packaging)",
        blank=True
    )
    published = models.BooleanField(
        default=True,
        db_index=True,  # Índice para filtrado rápido
        help_text="Indica si el producto está visible públicamente"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True  # Índice para ordenamiento
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['-created_at', 'published']),
            models.Index(fields=['user', 'published']),
        ]

    def save(self, *args, **kwargs):
        self.key = saveSystemCode(Product, self.key, self.pk, 'prod_')
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.key} - {self.Product_base.title if self.Product_base else 'Sin base'}"


class Image(models.Model):
    """
    Galería de imágenes adicionales para un producto.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='product_images'  # ✅ CORREGIDO: era 'prosuct_images'
    )
    image = ThumbnailerImageField(
        upload_to='images/products/gallery', 
        max_length=255, 
        resize_source=dict(size=(0, 1300), crop=True),
        help_text="Imagen adicional del producto"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Imagen de producto'
        verbose_name_plural = 'Imágenes de productos'

    def __str__(self):
        return f"Imagen de {self.product.key}"