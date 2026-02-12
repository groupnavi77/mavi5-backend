# core/product_ins/admin.py
"""
Admin personalizado para el módulo de Productos (Product Instances).
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django import forms
from easy_thumbnails.files import get_thumbnailer

from .models import Product, Image


# ============================================================================
# INLINE PARA IMÁGENES ADICIONALES
# ============================================================================

class ImageInline(admin.TabularInline):
    """Inline para gestionar la galería de imágenes del producto"""
    model = Image
    extra = 1
    fields = ['image', 'image_preview', 'created_at']
    readonly_fields = ['image_preview', 'created_at']
    
    def image_preview(self, obj):
        """Muestra preview de la imagen en el inline"""
        if obj.image:
            try:
                thumbnail = get_thumbnailer(obj.image)['img316']
                return format_html(
                    '<img src="{}" style="max-height: 80px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                    thumbnail.url
                )
            except:
                return format_html('<span style="color: #9ca3af;">Error al cargar imagen</span>')
        return format_html('<span style="color: #9ca3af;">Sin imagen</span>')
    image_preview.short_description = 'Preview'


# ============================================================================
# FORM PERSONALIZADO
# ============================================================================

class ProductAdminForm(forms.ModelForm):
    """Form con validaciones y widgets personalizados"""
    
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descripción personalizada del producto...',
                'style': 'width: 100%;'
            }),
            'key': forms.TextInput(attrs={
                'placeholder': 'Se genera automáticamente si se deja vacío',
                'style': 'width: 100%;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Key es auto-generado
        if 'key' in self.fields:
            self.fields['key'].required = False
            self.fields['key'].help_text = "💡 Dejar vacío para generar automáticamente"
        
        # Mejorar help texts
        if 'Product_base' in self.fields:
            self.fields['Product_base'].help_text = "📦 Producto base (plantilla)"
        
        if 'user' in self.fields:
            self.fields['user'].help_text = "👤 Usuario creador"
        
        if 'tag' in self.fields:
            self.fields['tag'].help_text = "🏷️ Ej: oferta, nuevo, destacado, verano"


# ============================================================================
# ADMIN DE PRODUCT
# ============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin mejorado para productos con filtros, búsqueda y acciones masivas"""
    
    form = ProductAdminForm
    inlines = [ImageInline]
    
    # ========================================================================
    # LIST DISPLAY
    # ========================================================================
    
    list_display = [
        'id_badge',
        'image_preview_list',
        'key_display',
        'product_base_info',
        'user_display',
        'tags_display',
        'images_count_badge',
        'status_badge',
        'created_at_display',
    ]
    
    list_display_links = ['key_display']
    
    # ========================================================================
    # FILTROS Y BÚSQUEDA
    # ========================================================================
    
    list_filter = [
        'published',
        'created_at',
        'updated_at',
        'Product_base',
        'user',
    ]
    
    search_fields = [
        'key',
        'description',
        'Product_base__title',
        'Product_base__key',
        'user__email',
        'user__first_name',
        'user__last_name',
        'tag__name',
    ]
    
    # ========================================================================
    # CONFIGURACIÓN
    # ========================================================================
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    
    readonly_fields = [
        'key',
        'created_at',
        'updated_at',
        'image_preview_large',
        'gallery_preview',
        'quick_stats',
    ]
    
    autocomplete_fields = ['Product_base', 'user']
    
    # ========================================================================
    # FIELDSETS
    # ========================================================================
    
    fieldsets = (
        ('📋 INFORMACIÓN BÁSICA', {
            'fields': ('key', 'Product_base', 'user'),
            'description': mark_safe('''
                <div style="background: #dbeafe; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <strong style="color: #1e40af;">💡 Información del Producto</strong>
                    <ul style="margin: 8px 0; color: #1e3a8a;">
                        <li><strong>Key:</strong> Se genera automáticamente al guardar</li>
                        <li><strong>Product Base:</strong> Plantilla base del producto</li>
                        <li><strong>Usuario:</strong> Creador del producto</li>
                    </ul>
                </div>
            ''')
        }),
        
        ('🖼️ IMAGEN PRINCIPAL', {
            'fields': ('image', 'image_preview_large'),
        }),
        
        ('📝 DESCRIPCIÓN Y TAGS', {
            'fields': ('description', 'tag'),
        }),
        
        ('⚙️ CONFIGURACIÓN', {
            'fields': ('published', 'quick_stats'),
        }),
        
        ('🖼️ GALERÍA DE IMÁGENES', {
            'fields': ('gallery_preview',),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div style="background: #fef3c7; padding: 12px; border-radius: 6px; margin: 10px 0;">
                    <strong style="color: #92400e;">📸 Galería:</strong>
                    <span style="color: #78350f;">Agrega imágenes adicionales en la sección de "Imágenes de producto" abajo</span>
                </div>
            ''')
        }),
        
        ('📅 METADATA', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # ========================================================================
    # MÉTODOS DE LIST_DISPLAY
    # ========================================================================
    
    def id_badge(self, obj):
        """Badge con el ID"""
        return format_html(
            '<span style="background: #3b82f6; color: white; padding: 4px 10px; '
            'border-radius: 12px; font-weight: 700; font-family: monospace;">#{}</span>',
            obj.id
        )
    id_badge.short_description = 'ID'
    id_badge.admin_order_field = 'id'
    
    def image_preview_list(self, obj):
        """Preview pequeño de la imagen en el listado"""
        if obj.image:
            try:
                thumbnail = get_thumbnailer(obj.image)['img316']
                return format_html(
                    '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; '
                    'border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                    thumbnail.url
                )
            except:
                return format_html('<span style="color: #ef4444;">❌</span>')
        return format_html(
            '<div style="width: 60px; height: 60px; background: #f3f4f6; '
            'border-radius: 8px; display: flex; align-items: center; justify-content: center; '
            'color: #9ca3af; font-size: 24px;">📷</div>'
        )
    image_preview_list.short_description = '🖼️'
    
    def key_display(self, obj):
        """Key con formato"""
        return format_html(
            '<code style="background: #f3f4f6; padding: 6px 10px; border-radius: 6px; '
            'font-size: 12px; color: #1f2937; font-family: monospace;">{}</code>',
            obj.key or 'Sin key'
        )
    key_display.short_description = 'Key'
    key_display.admin_order_field = 'key'
    
    def product_base_info(self, obj):
        """Información del ProductBase"""
        if obj.Product_base:
            return format_html(
                '<div style="line-height: 1.6;">'
                '<strong style="color: #1f2937;">{}</strong><br>'
                '<small style="color: #6b7280;">Key: {}</small>'
                '</div>',
                obj.Product_base.title[:30] + '...' if len(obj.Product_base.title) > 30 else obj.Product_base.title,
                obj.Product_base.key or 'N/A'
            )
        return format_html('<span style="color: #9ca3af;">Sin base</span>')
    product_base_info.short_description = 'Producto Base'
    product_base_info.admin_order_field = 'Product_base__title'
    
    def user_display(self, obj):
        """Usuario creador"""
        if obj.user:
            name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="background: #e0e7ff; color: #4338ca; padding: 4px 8px; '
                'border-radius: 10px; font-size: 11px; font-weight: 600;">👤</span>'
                '<span style="color: #374151;">{}</span>'
                '</div>',
                name[:25] + '...' if len(name) > 25 else name
            )
        return format_html('<span style="color: #9ca3af;">Sin usuario</span>')
    user_display.short_description = 'Usuario'
    user_display.admin_order_field = 'user__email'
    
    def tags_display(self, obj):
        """Tags con badges"""
        tags = list(obj.tag.all()[:3])
        
        if not tags:
            return format_html('<span style="color: #9ca3af;">Sin tags</span>')
        
        tags_html = ''
        for tag in tags:
            tags_html += format_html(
                '<span style="background: #e0e7ff; color: #4338ca; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; margin-right: 4px; '
                'display: inline-block; margin-bottom: 2px;">{}</span>',
                tag.name
            )
        
        total_tags = obj.tag.count()
        if total_tags > 3:
            tags_html += format_html(
                '<span style="color: #6b7280; font-size: 11px;">+{}</span>',
                total_tags - 3
            )
        
        return format_html('<div style="max-width: 200px;">{}</div>', mark_safe(tags_html))
    tags_display.short_description = 'Tags'
    
    def images_count_badge(self, obj):
        """Contador de imágenes adicionales"""
        count = obj.product_images.count()
        
        if count == 0:
            color = '#9ca3af'
            icon = '📷'
        elif count <= 3:
            color = '#10b981'
            icon = '🖼️'
        else:
            color = '#3b82f6'
            icon = '🎨'
        
        return format_html(
            '<div style="text-align: center;">'
            '<span style="background: {}; color: white; padding: 4px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{} {}</span>'
            '</div>',
            color, icon, count
        )
    images_count_badge.short_description = 'Galería'
    
    def status_badge(self, obj):
        """Badge de estado publicado/no publicado"""
        if obj.published:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 6px 14px; '
                'border-radius: 15px; font-size: 11px; font-weight: 600; '
                'display: inline-flex; align-items: center; gap: 6px;">'
                '<span style="display: inline-block; width: 8px; height: 8px; '
                'background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>'
                '✓ PUBLICADO'
                '</span>'
            )
        return format_html(
            '<span style="background: #ef4444; color: white; padding: 6px 14px; '
            'border-radius: 15px; font-size: 11px; font-weight: 600;">'
            '○ BORRADOR'
            '</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'published'
    
    def created_at_display(self, obj):
        """Fecha de creación con formato"""
        return format_html(
            '<div style="line-height: 1.5;">'
            '<div style="color: #374151; font-weight: 500;">{}</div>'
            '<div style="color: #9ca3af; font-size: 11px;">{}</div>'
            '</div>',
            obj.created_at.strftime('%d/%m/%Y'),
            obj.created_at.strftime('%H:%M')
        )
    created_at_display.short_description = 'Creado'
    created_at_display.admin_order_field = 'created_at'
    
    # ========================================================================
    # MÉTODOS READONLY
    # ========================================================================
    
    def image_preview_large(self, obj):
        """Preview grande de la imagen principal"""
        if obj.image:
            try:
                thumbnail = get_thumbnailer(obj.image)['img316']
                return format_html(
                    '<div style="margin: 15px 0;">'
                    '<img src="{}" style="max-width: 500px; max-height: 400px; '
                    'border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); '
                    'display: block; margin-bottom: 15px;" />'
                    '<div style="display: flex; gap: 10px;">'
                    '<a href="{}" target="_blank" style="background: #3b82f6; color: white; '
                    'text-decoration: none; padding: 12px 24px; border-radius: 8px; '
                    'font-weight: 600; display: inline-flex; align-items: center; gap: 8px;">'
                    '🔗 Ver imagen completa'
                    '</a>'
                    '</div>'
                    '</div>',
                    thumbnail.url,
                    obj.image.url
                )
            except:
                return format_html(
                    '<div style="padding: 30px; background: #fef2f2; border-radius: 8px; '
                    'text-align: center; color: #ef4444;">'
                    '❌ Error al cargar la imagen'
                    '</div>'
                )
        return format_html(
            '<div style="padding: 40px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); '
            'border-radius: 10px; text-align: center; border: 2px dashed #9ca3af;">'
            '<div style="font-size: 48px; margin-bottom: 12px;">📷</div>'
            '<div style="color: #6b7280; font-size: 16px; font-weight: 600;">No hay imagen principal</div>'
            '<div style="color: #9ca3af; font-size: 13px; margin-top: 8px;">Sube una imagen arriba</div>'
            '</div>'
        )
    image_preview_large.short_description = 'Vista Previa'
    
    def gallery_preview(self, obj):
        """Preview de la galería de imágenes"""
        images = obj.product_images.all()
        
        if not images:
            return format_html(
                '<div style="padding: 30px; background: #f9fafb; border-radius: 8px; '
                'text-align: center; color: #6b7280;">'
                '🖼️ No hay imágenes adicionales en la galería'
                '</div>'
            )
        
        gallery_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px;">'
        
        for img in images:
            try:
                thumbnail = get_thumbnailer(img.image)['img316']
                gallery_html += format_html(
                    '<div style="position: relative; border-radius: 8px; overflow: hidden; '
                    'box-shadow: 0 4px 6px rgba(0,0,0,0.1);">'
                    '<img src="{}" style="width: 100%; height: 150px; object-fit: cover;" />'
                    '<div style="position: absolute; bottom: 0; left: 0; right: 0; '
                    'background: rgba(0,0,0,0.6); color: white; padding: 6px; '
                    'font-size: 11px; text-align: center;">'
                    '{}'
                    '</div>'
                    '</div>',
                    thumbnail.url,
                    img.created_at.strftime('%d/%m/%Y')
                )
            except:
                gallery_html += '<div style="background: #fee2e2; padding: 20px; border-radius: 8px; text-align: center;">❌</div>'
        
        gallery_html += '</div>'
        
        return format_html(gallery_html)
    gallery_preview.short_description = 'Galería'
    
    def quick_stats(self, obj):
        """Estadísticas rápidas del producto"""
        if not obj.pk:
            return "Guarda el producto para ver estadísticas"
        
        images_count = obj.product_images.count()
        tags_count = obj.tag.count()
        
        return format_html(
            '<div style="background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); '
            'padding: 20px; border-radius: 10px; color: white;">'
            '<h3 style="margin: 0 0 15px 0; font-size: 16px;">📊 Estadísticas Rápidas</h3>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">'
            
            '<div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">'
            '<div style="font-size: 11px; opacity: 0.9; margin-bottom: 5px;">IMÁGENES GALERÍA</div>'
            '<div style="font-size: 32px; font-weight: 700;">{}</div>'
            '</div>'
            
            '<div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">'
            '<div style="font-size: 11px; opacity: 0.9; margin-bottom: 5px;">TAGS ASIGNADOS</div>'
            '<div style="font-size: 32px; font-weight: 700;">{}</div>'
            '</div>'
            
            '</div>'
            '</div>',
            images_count,
            tags_count
        )
    quick_stats.short_description = 'Estadísticas'
    
    # ========================================================================
    # ACCIONES MASIVAS
    # ========================================================================
    
    actions = [
        'publish_products',
        'unpublish_products',
        'duplicate_products',
        'clear_tags',
    ]
    
    @admin.action(description='✅ Publicar productos seleccionados')
    def publish_products(self, request, queryset):
        count = queryset.update(published=True)
        self.message_user(request, f'✅ {count} producto(s) publicado(s)')
    
    @admin.action(description='📝 Convertir a borrador')
    def unpublish_products(self, request, queryset):
        count = queryset.update(published=False)
        self.message_user(request, f'📝 {count} producto(s) convertido(s) a borrador')
    
    @admin.action(description='🔄 Duplicar productos')
    def duplicate_products(self, request, queryset):
        count = 0
        for product in queryset:
            # Guardar tags antes de duplicar
            tags = list(product.tag.all())
            
            # Duplicar producto
            product.pk = None
            product.key = None  # Se generará uno nuevo
            product.published = False
            product.save()
            
            # Copiar tags
            for tag in tags:
                product.tag.add(tag)
            
            count += 1
        
        self.message_user(request, f'🔄 {count} producto(s) duplicado(s)')
    
    @admin.action(description='🏷️ Limpiar todos los tags')
    def clear_tags(self, request, queryset):
        count = 0
        for product in queryset:
            product.tag.clear()
            count += 1
        self.message_user(request, f'🏷️ Tags eliminados de {count} producto(s)')
    
    # ========================================================================
    # MÉTODOS ADICIONALES
    # ========================================================================
    
    def get_queryset(self, request):
        """Optimiza el queryset para evitar N+1 queries"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'Product_base',
            'user'
        ).prefetch_related(
            'tag',
            'product_images'
        ).annotate(
            images_count=Count('product_images')
        )


# ============================================================================
# ADMIN DE IMAGE (OPCIONAL - SOLO SI QUIERES GESTIONAR DIRECTAMENTE)
# ============================================================================

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Admin simple para gestión directa de imágenes"""
    
    list_display = ['id', 'product_display', 'image_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__key', 'product__description']
    readonly_fields = ['image_preview_large', 'created_at']
    
    fieldsets = (
        ('📦 PRODUCTO', {
            'fields': ('product',),
        }),
        ('🖼️ IMAGEN', {
            'fields': ('image', 'image_preview_large'),
        }),
        ('📅 METADATA', {
            'fields': ('created_at',),
        }),
    )
    
    def product_display(self, obj):
        """Información del producto"""
        return format_html(
            '<strong>{}</strong><br><small style="color: #6b7280;">{}</small>',
            obj.product.key,
            obj.product.Product_base.title if obj.product.Product_base else 'Sin base'
        )
    product_display.short_description = 'Producto'
    
    def image_preview(self, obj):
        """Preview pequeño"""
        if obj.image:
            try:
                thumbnail = get_thumbnailer(obj.image)['img316']
                return format_html(
                    '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; '
                    'border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                    thumbnail.url
                )
            except:
                return '❌'
        return '📷'
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        """Preview grande"""
        if obj.image:
            try:
                thumbnail = get_thumbnailer(obj.image)['img316']
                return format_html(
                    '<img src="{}" style="max-width: 500px; border-radius: 10px; '
                    'box-shadow: 0 10px 25px rgba(0,0,0,0.15);" />',
                    thumbnail.url
                )
            except:
                return 'Error al cargar imagen'
        return 'Sin imagen'
    image_preview_large.short_description = 'Vista Previa'