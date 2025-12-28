# models.py - Slider con campo de imagen
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from easy_thumbnails.fields import ThumbnailerImageField

class Slider(models.Model):
    """Slider flexible con slug único"""
    
    SECTION_CHOICES = [
        ('home_hero', 'Home - Hero Banner'),
        ('home_deals', 'Home - Ofertas'),
        ('home_categories', 'Home - Categorías'),
        ('product_banner', 'Producto - Banner'),
        ('category_banner', 'Categoría - Banner'),
        ('checkout_promo', 'Checkout - Promoción'),
        ('blog_featured', 'Blog - Destacado'),
        ('seasonal', 'Campaña Temporal'),
        ('footer_promo', 'Footer - Promoción'),
        ('custom', 'Personalizado'),
    ]
    
    section = models.CharField(
        _("Sección"),
        max_length=50,
        choices=SECTION_CHOICES,
        default='home_hero',
        db_index=True,
        help_text="Sección donde se mostrará este slider"
    )
    
    title = models.CharField(
        _("Título interno"), 
        max_length=200, 
        help_text="Solo para admin"
    )
    
    # ✨ SLUG para URLs amigables
    slug = models.SlugField(
        _("Slug"),
        max_length=200,
        unique=True,
        help_text="URL amigable (se genera automáticamente si está vacío)"
    )
    
    # Imagen
    image = ThumbnailerImageField(
        _("Imagen"),
        upload_to='sliders/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        help_text="Formatos: JPG, PNG, WEBP, GIF. Máx 5MB"
    )
    
    # Contenido JSON
    content = models.JSONField(
        _("Contenido"), 
        default=dict,
        help_text="Estructura JSON con contenido adicional"
    )
    
    # Configuración
    order = models.IntegerField(_("Orden"), default=0)
    is_active = models.BooleanField(_("Activo"), default=True)
    
    # Programación opcional
    start_date = models.DateTimeField(
        _("Fecha de inicio"), 
        null=True, 
        blank=True
    )
    end_date = models.DateTimeField(
        _("Fecha de fin"), 
        null=True, 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Slider")
        verbose_name_plural = _("Sliders")
        ordering = ['section', 'order', '-created_at']
        indexes = [
            models.Index(fields=['section', 'is_active', 'order']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"#{self.id} - {self.get_section_display()} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Auto-generar slug si está vacío"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Asegurar que el slug sea único
            while Slider.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def get_content_field(self, field_name, default=None):
        """Helper para obtener campos del JSON"""
        return self.content.get(field_name, default)
    
    @property
    def image_url(self):
        """Retorna la URL de la imagen"""
        if self.image:
            return self.image.url
        return None
    
    def is_currently_active(self):
        """Verifica si el slider está activo según fechas"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True

