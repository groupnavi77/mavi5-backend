# core/configuration/models.py - ACTUALIZADO

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from easy_thumbnails.fields import ThumbnailerImageField
from mptt.models import MPTTModel, TreeForeignKey
from tinymce.models import HTMLField


"""
MODELOS DE CONFIGURACIÓN DEL SITIO
==================================

Este módulo contiene:
1. Slider - Sistema de banners/sliders
2. Menu - Sistema de menús jerárquicos (tipo WordPress)
3. Page - Páginas estáticas (Privacidad, Términos, etc)
"""


# ============================================================================
# MODELO SLIDER (YA EXISTENTE)
# ============================================================================

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
    
    slug = models.SlugField(
        _("Slug"),
        max_length=200,
        unique=True,
        help_text="URL amigable (se genera automáticamente si está vacío)"
    )
    
    image = ThumbnailerImageField(
        _("Imagen"),
        upload_to='sliders/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        help_text="Formatos: JPG, PNG, WEBP, GIF. Máx 5MB"
    )
    
    content = models.JSONField(
        _("Contenido"), 
        default=dict,
        help_text="Estructura JSON con contenido adicional"
    )
    
    order = models.IntegerField(_("Orden"), default=0)
    is_active = models.BooleanField(_("Activo"), default=True)
    
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


# ============================================================================
# MODELO MENU (NUEVO)
# ============================================================================

class Menu(MPTTModel):
    """
    Sistema de menús jerárquicos flexible tipo WordPress.
    Soporta menús multinivel, iconos, clases CSS personalizadas, y múltiples tipos de enlaces.
    """
    
    # Tipos de menú
    MENU_TYPE_CHOICES = [
        ('header', 'Menú Principal (Header)'),
        ('footer', 'Menú Footer'),
        ('mobile', 'Menú Móvil'),
        ('sidebar', 'Menú Lateral'),
        ('custom', 'Personalizado'),
    ]
    
    # Tipos de enlace
    LINK_TYPE_CHOICES = [
        ('url', 'URL Personalizada'),
        ('category', 'Categoría'),
        ('page', 'Página'),
        ('external', 'Enlace Externo'),
        ('megamenu', 'Mega Menú'),
    ]
    
    # Información básica
    name = models.CharField(
        _("Nombre"),
        max_length=100,
        help_text="Texto que se mostrará en el menú"
    )
    
    slug = models.SlugField(
        _("Slug"),
        max_length=100,
        unique=True,
        help_text="Se genera automáticamente del nombre"
    )
    
    # Jerarquía MPTT
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Menú Padre"),
        help_text="Dejar vacío para menú de nivel raíz"
    )
    
    # Tipo y ubicación
    menu_type = models.CharField(
        _("Tipo de Menú"),
        max_length=20,
        choices=MENU_TYPE_CHOICES,
        default='header',
        db_index=True,
        help_text="Ubicación donde se mostrará este menú"
    )
    
    link_type = models.CharField(
        _("Tipo de Enlace"),
        max_length=20,
        choices=LINK_TYPE_CHOICES,
        default='url',
        help_text="Tipo de contenido que enlaza este menú"
    )
    
    # URL y enlaces
    url = models.CharField(
        _("URL"),
        max_length=500,
        blank=True,
        null=True,
        help_text="URL personalizada (ej: /shop, /about, https://external.com)"
    )
    
    # Relaciones opcionales
    category = models.ForeignKey(
        'category.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items',
        verbose_name=_("Categoría"),
        help_text="Categoría a la que enlaza (solo si link_type='category')"
    )
    
    page = models.ForeignKey(
        'Page',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items',
        verbose_name=_("Página"),
        help_text="Página a la que enlaza (solo si link_type='page')"
    )
    
    # Visual
    icon = models.CharField(
        _("Icono"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Clase de icono (ej: fa-home, bi-cart, lucide-menu)"
    )
    
    image = ThumbnailerImageField(
        _("Imagen"),
        upload_to='menus/%Y/%m/',
        blank=True,
        null=True,
        help_text="Imagen opcional para mega menús"
    )
    
    # Descripción y metadata
    description = models.TextField(
        _("Descripción"),
        max_length=500,
        blank=True,
        null=True,
        help_text="Descripción que aparece al hacer hover o en mega menús"
    )
    
    # Clases CSS personalizadas
    css_classes = models.CharField(
        _("Clases CSS"),
        max_length=255,
        blank=True,
        null=True,
        help_text="Clases CSS separadas por espacios (ej: btn-primary highlight featured)"
    )
    
    # Atributos HTML personalizados (JSON)
    attributes = models.JSONField(
        _("Atributos HTML"),
        default=dict,
        blank=True,
        help_text="Atributos HTML personalizados en formato JSON"
    )
    
    # Configuración
    order = models.IntegerField(
        _("Orden"),
        default=0,
        help_text="Orden de visualización (menor número = primero)"
    )
    
    is_active = models.BooleanField(
        _("Activo"),
        default=True,
        db_index=True,
        help_text="Mostrar/ocultar este item del menú"
    )
    
    open_in_new_tab = models.BooleanField(
        _("Abrir en nueva pestaña"),
        default=False,
        help_text="Agregar target='_blank' al enlace"
    )
    
    is_featured = models.BooleanField(
        _("Destacado"),
        default=False,
        help_text="Marcar como destacado (para estilos especiales)"
    )
    
    # Mega menú settings
    mega_menu_columns = models.IntegerField(
        _("Columnas de Mega Menú"),
        default=1,
        help_text="Número de columnas si es mega menú (1-6)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['menu_type', 'order', 'name']
    
    class Meta:
        verbose_name = _("Menú")
        verbose_name_plural = _("Menús")
        ordering = ['menu_type', 'tree_id', 'lft']
        indexes = [
            models.Index(fields=['menu_type', 'is_active', 'order']),
            models.Index(fields=['slug']),
            models.Index(fields=['link_type']),
        ]
    
    def __str__(self):
        return f"{self.get_menu_type_display()} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generar slug y validaciones"""
        # Generar slug automáticamente
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while Menu.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validaciones personalizadas"""
        # Validar que tenga URL o relación según link_type
        if self.link_type == 'url' and not self.url:
            raise ValidationError({
                'url': 'Se requiere una URL para el tipo de enlace "URL Personalizada"'
            })
        
        if self.link_type == 'category' and not self.category:
            raise ValidationError({
                'category': 'Se requiere seleccionar una categoría para el tipo de enlace "Categoría"'
            })
        
        if self.link_type == 'page' and not self.page:
            raise ValidationError({
                'page': 'Se requiere seleccionar una página para el tipo de enlace "Página"'
            })
    
    def get_url(self):
        """
        Obtiene la URL final del menú según su tipo.
        """
        if self.link_type == 'url':
            return self.url or '#'
        
        elif self.link_type == 'category' and self.category:
            return f'/products/{self.category.slug}'
        
        elif self.link_type == 'page' and self.page:
            return f'/page/{self.page.slug}'
        
        elif self.link_type == 'external':
            return self.url or '#'
        
        elif self.link_type == 'megamenu':
            return '#'  # Mega menús no tienen URL directa
        
        return '#'
    
    def get_css_classes_list(self):
        """Retorna las clases CSS como lista."""
        if self.css_classes:
            return self.css_classes.split()
        return []
    
    def has_children(self):
        """Verifica si tiene items hijos."""
        return self.get_children().exists()
    
    def get_active_children(self):
        """Obtiene solo los hijos activos."""
        return self.get_children().filter(is_active=True)
    
    @property
    def image_url(self):
        """Retorna la URL de la imagen si existe."""
        if self.image:
            return self.image.url
        return None


# ============================================================================
# MODELO PAGE (NUEVO)
# ============================================================================

class Page(models.Model):
    """
    Páginas estáticas del sitio (legales, institucionales, etc).
    Similar a las páginas de WordPress.
    """
    
    # Tipos de página
    PAGE_TYPE_CHOICES = [
        ('legal', 'Legal'),
        ('about', 'Institucional'),
        ('help', 'Ayuda/Soporte'),
        ('policy', 'Políticas'),
        ('custom', 'Personalizada'),
    ]
    
    # Plantillas disponibles
    TEMPLATE_CHOICES = [
        ('default', 'Plantilla por Defecto'),
        ('full_width', 'Ancho Completo'),
        ('sidebar', 'Con Sidebar'),
        ('landing', 'Landing Page'),
        ('contact', 'Contacto'),
    ]
    
    # Información básica
    title = models.CharField(
        _("Título"),
        max_length=200,
        help_text="Título de la página (se muestra en el navegador y H1)"
    )
    
    slug = models.SlugField(
        _("Slug"),
        max_length=200,
        unique=True,
        help_text="URL amigable (se genera automáticamente)"
    )
    
    # Tipo y categorización
    page_type = models.CharField(
        _("Tipo de Página"),
        max_length=20,
        choices=PAGE_TYPE_CHOICES,
        default='custom',
        db_index=True,
        help_text="Categoría de la página"
    )
    
    template = models.CharField(
        _("Plantilla"),
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='default',
        help_text="Plantilla de diseño a usar"
    )
    
    # Contenido
    content = HTMLField(
        _("Contenido"),
        help_text="Contenido principal de la página (HTML con TinyMCE)"
    )
    
    excerpt = models.TextField(
        _("Extracto"),
        max_length=500,
        blank=True,
        null=True,
        help_text="Resumen corto para meta description y previews"
    )
    
    # Imagen destacada
    featured_image = ThumbnailerImageField(
        _("Imagen Destacada"),
        upload_to='pages/%Y/%m/',
        blank=True,
        null=True,
        help_text="Imagen principal de la página"
    )
    
    # SEO
    meta_title = models.CharField(
        _("Meta Título"),
        max_length=70,
        blank=True,
        null=True,
        help_text="Título para SEO (máx 70 caracteres). Si vacío, usa el título principal"
    )
    
    meta_description = models.CharField(
        _("Meta Descripción"),
        max_length=160,
        blank=True,
        null=True,
        help_text="Descripción para SEO (máx 160 caracteres). Si vacío, usa el extracto"
    )
    
    meta_keywords = models.CharField(
        _("Meta Keywords"),
        max_length=255,
        blank=True,
        null=True,
        help_text="Palabras clave separadas por comas"
    )
    
    # Configuración
    is_published = models.BooleanField(
        _("Publicado"),
        default=True,
        db_index=True,
        help_text="Mostrar/ocultar página"
    )
    
    show_in_menu = models.BooleanField(
        _("Mostrar en Menú"),
        default=False,
        help_text="Sugerir esta página para menús automáticos"
    )
    
    require_auth = models.BooleanField(
        _("Requiere Autenticación"),
        default=False,
        help_text="Solo usuarios logueados pueden ver esta página"
    )
    
    order = models.IntegerField(
        _("Orden"),
        default=0,
        help_text="Orden de visualización en listados"
    )
    
    # Timestamps
    published_at = models.DateTimeField(
        _("Fecha de Publicación"),
        null=True,
        blank=True,
        help_text="Programar publicación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Autor (opcional - puedes relacionar con User si lo necesitas)
    # author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = _("Página")
        verbose_name_plural = _("Páginas")
        ordering = ['page_type', 'order', 'title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['page_type', 'is_published']),
            models.Index(fields=['is_published', 'published_at']),
        ]
    
    def __str__(self):
        return f"{self.get_page_type_display()} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Auto-generar slug y meta fields"""
        # Generar slug
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            while Page.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Auto-generar meta_title si está vacío
        if not self.meta_title:
            self.meta_title = self.title[:70]
        
        # Auto-generar meta_description si está vacío
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        # Set published_at si se publica por primera vez
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def is_currently_published(self):
        """Verifica si la página está publicada actualmente."""
        if not self.is_published:
            return False
        
        if self.published_at and self.published_at > timezone.now():
            return False
        
        return True
    
    def get_absolute_url(self):
        """Retorna la URL de la página."""
        return f'/page/{self.slug}'
    
    @property
    def featured_image_url(self):
        """Retorna la URL de la imagen destacada."""
        if self.featured_image:
            return self.featured_image.url
        return None
    
    def get_reading_time(self):
        """Calcula el tiempo estimado de lectura (palabras / 200)."""
        from django.utils.html import strip_tags
        text = strip_tags(self.content)
        word_count = len(text.split())
        return max(1, round(word_count / 200))