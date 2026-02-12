# core/product_base/admin.py - ADMIN ULTRA MEJORADO

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.db.models import Count, Min, Max, Q
from django.utils import timezone
import json

from .models import ProductBase, ImageProductBase, Price, Discount
from core.category.models import Category


# ============================================================================
# WIDGET PERSONALIZADO PARA TAGS
# ============================================================================

class HashtagAutocompleteWidget(forms.TextInput):
    """Widget mejorado para autocompletado de tags"""
    template_name = 'django/forms/widgets/input.html'
    
    @property
    def media(self):
        return forms.Media(
            js=[
                'admin/js/core.js',
                'admin/js/jquery.init.js',
                'admin-static/js/hashtag-admin.js'
            ]
        )
    
    def format_value(self, value):
        """Convierte tags a formato string separado por comas"""
        if isinstance(value, str):
            return value
        
        if not value:
            return ''
        
        tags_to_join = None

        if hasattr(value, 'all'):
            tags_to_join = value.all()
        elif hasattr(value, '__iter__'):
            tags_to_join = value
        
        if tags_to_join is not None:
            return ', '.join(tag.name for tag in tags_to_join)
            
        return value


# ============================================================================
# INLINES MEJORADOS
# ============================================================================

class PriceInlineForm(forms.ModelForm):
    """Form mejorado para Price inline"""
    
    class Meta:
        model = Price
        fields = '__all__'
        widgets = {
            'price': forms.NumberInput(attrs={
                'style': 'width: 120px;',
                'min': '0',
                'step': '0.01'
            }),
            'quantity': forms.NumberInput(attrs={
                'style': 'width: 100px;',
                'min': '1'
            }),
            'discount': forms.NumberInput(attrs={
                'style': 'width: 100px;',
                'min': '0',
                'step': '0.01'
            }),
            'time_production': forms.NumberInput(attrs={
                'style': 'width: 80px;',
                'min': '1'
            }),
        }


class PriceInline(admin.TabularInline):
    """Inline mejorado para precios"""
    model = Price
    form = PriceInlineForm
    extra = 1
    min_num = 1
    
    fields = ['quantity', 'unit', 'price', 'discount', 'discount_type', 'time_production']
    
    verbose_name = "Precio por Cantidad"
    verbose_name_plural = "📊 Tabla de Precios por Cantidad"
    
    def get_extra(self, request, obj=None, **kwargs):
        """Solo muestra 1 fila extra si es nuevo, 0 si ya existe"""
        if obj:
            return 0
        return 1


class DiscountInline(admin.TabularInline):
    """Inline mejorado para descuentos"""
    model = Discount
    extra = 0
    
    fields = ['discount', 'discount_type', 'start_date', 'expiration_date']
    
    verbose_name = "Descuento Temporal"
    verbose_name_plural = "🎁 Descuentos Temporales del Producto"
    
    def get_queryset(self, request):
        """Muestra descuentos ordenados por fecha de inicio"""
        qs = super().get_queryset(request)
        return qs.order_by('-start_date')


class MediaProductBaseInline(admin.TabularInline):
    """Inline mejorado para galería de imágenes"""
    model = ImageProductBase
    extra = 1
    
    fields = ['image', 'image_preview']
    readonly_fields = ['image_preview']
    
    verbose_name = "Imagen de Galería"
    verbose_name_plural = "🖼️ Galería de Imágenes Adicionales"
    
    def image_preview(self, obj):
        """Preview de imagen en inline"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 100px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'


# ============================================================================
# FORM PRINCIPAL
# ============================================================================

class ProductBaseAdminForm(forms.ModelForm):
    """Form con validaciones avanzadas y categorías jerárquicas"""
    
    class Meta:
        model = ProductBase
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Ej: Tarjetas de Presentación Premium',
                'style': 'width: 100%; font-size: 14px;',
                'class': 'vTextField'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'tarjetas-de-presentacion-premium (se genera automático)',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descripción breve para listados y SEO (máx 500 caracteres)',
                'style': 'width: 100%;',
                'maxlength': 500
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar slug
        if 'slug' in self.fields:
            if not self.instance.pk:
                self.fields['slug'].required = False
                self.fields['slug'].help_text = "💡 Dejar vacío para generar del título"
        
        # ✨ CONFIGURAR CATEGORÍAS JERÁRQUICAS
        if 'category' in self.fields:
            self.fields['category'].help_text = "📂 Categoría principal del producto (jerarquía visual)"
            
            # Obtener todas las categorías ordenadas por árbol MPTT
            categories = Category.objects.all().order_by('tree_id', 'lft')
            
            # Crear choices con indentación visual y emojis
            choices = [('', '— Seleccionar categoría —')]
            
            for cat in categories:
                # Indentación según nivel
                indent = '  ' * cat.level  # 2 espacios por nivel
                
                # Emojis según nivel para mejor visualización
                if cat.level == 0:
                    icon = '📁'  # Carpeta - Raíz
                    prefix = ''
                elif cat.level == 1:
                    icon = '📂'  # Carpeta abierta
                    prefix = '├─ '
                else:
                    icon = '📄'  # Documento
                    prefix = '  └─ '
                
                # Construir label con indentación e icono
                label = f"{indent}{prefix}{icon} {cat.title}"
                
                # Agregar conteo de productos si existe
                products_count = cat.products.count() if hasattr(cat, 'products') else 0
                if products_count > 0:
                    label += f" ({products_count})"
                
                choices.append((cat.pk, label))
            
            # Aplicar choices
            self.fields['category'].choices = choices
            
            # Estilo para el select
            self.fields['category'].widget.attrs.update({
                'style': 'width: 100%; font-family: "Courier New", monospace; font-size: 13px; padding: 8px;',
                'class': 'category-select-hierarchical'
            })
        
        if 'published' in self.fields:
            self.fields['published'].help_text = "✅ Visible para usuarios en el sitio"
        
        if 'image' in self.fields:
            self.fields['image'].help_text = "📸 Imagen principal (PNG transparente recomendado)"
    
    def clean_short_description(self):
        """Validar longitud de descripción corta"""
        short_desc = self.cleaned_data.get('short_description', '')
        if short_desc and len(short_desc) > 500:
            raise ValidationError('⚠️ Máximo 500 caracteres')
        return short_desc


# ============================================================================
# ADMIN PRINCIPAL
# ============================================================================

@admin.register(ProductBase)
class ProductBaseAdmin(admin.ModelAdmin):
    """Admin ultra mejorado para ProductBase"""
    
    form = ProductBaseAdminForm
    
    list_display = [
        'id_badge',
        'image_preview_list',
        'title',
        'slug_display',
        'category_badge',
        'price_range_display',
        'tags_display',
        'status_badge',
        'stats_badge',
        'updated_at',
    ]
    
    list_display_links = ['title']
    list_filter = ['published', 'category', 'created_at', 'updated_at']
    search_fields = ['id', 'key', 'title', 'slug', 'short_description', 'tag__name']
    prepopulated_fields = {'slug': ('title',)}
    
    readonly_fields = [
        'id',
        'key',
        'created_at',
        'updated_at',
        'quick_guide',
        'image_preview_large',
        'image_info',
        'price_stats',
        'discount_stats',
        'product_stats'
    ]
    
    inlines = [MediaProductBaseInline, PriceInline, DiscountInline]
    
    fieldsets = (
        ('🎯 GUÍA RÁPIDA', {
            'fields': ('quick_guide',),
            'description': mark_safe('''
                <div style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0;">
                    <h2 style="margin: 0 0 20px 0; font-size: 22px;">🎯 Guía Rápida: Crear Producto Base</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px;">
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 18px; border-radius: 10px;">
                            <div style="font-size: 32px; margin-bottom: 10px;">1️⃣</div>
                            <h3 style="margin: 0 0 10px 0; font-size: 14px;">Info Básica</h3>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6;">
                                <li>Título claro</li>
                                <li>Categoría</li>
                                <li>Descripción SEO</li>
                            </ul>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 18px; border-radius: 10px;">
                            <div style="font-size: 32px; margin-bottom: 10px;">2️⃣</div>
                            <h3 style="margin: 0 0 10px 0; font-size: 14px;">Imagen</h3>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6;">
                                <li>PNG transparente</li>
                                <li>1300x1300px ideal</li>
                                <li>Producto centrado</li>
                            </ul>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 18px; border-radius: 10px;">
                            <div style="font-size: 32px; margin-bottom: 10px;">3️⃣</div>
                            <h3 style="margin: 0 0 10px 0; font-size: 14px;">Precios</h3>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6;">
                                <li>Mínimo 1 precio</li>
                                <li>Por cantidades</li>
                                <li>Unidades claras</li>
                            </ul>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 18px; border-radius: 10px;">
                            <div style="font-size: 32px; margin-bottom: 10px;">4️⃣</div>
                            <h3 style="margin: 0 0 10px 0; font-size: 14px;">Tags & Más</h3>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6;">
                                <li>Tags relevantes</li>
                                <li>Galería (opcional)</li>
                                <li>Descuentos (opcional)</li>
                            </ul>
                        </div>
                        
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <strong style="font-size: 15px;">✅ Checklist antes de publicar:</strong>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; font-size: 13px;">
                            <div>☑️ Título y descripción completos</div>
                            <div>☑️ Al menos 1 precio configurado</div>
                            <div>☑️ Categoría asignada</div>
                            <div>☑️ Imagen principal subida</div>
                            <div>☑️ Tags agregados</div>
                            <div>☑️ Publicado = ✅</div>
                        </div>
                    </div>
                </div>
            ''')
        }),
        
        ('🔢 IDENTIFICACIÓN', {
            'fields': ('id', 'key', 'title', 'slug'),
        }),
        
        ('📂 CATEGORÍA Y PUBLICACIÓN', {
            'fields': ('category', 'published'),
            'description': mark_safe('''
                <div style="background: #e0f2fe; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #0ea5e9;">
                    <strong style="color: #0369a1;">💡 Categorías Jerárquicas:</strong>
                    <p style="margin: 8px 0 12px 0; color: #0c4a6e;">
                        Las categorías se muestran en estructura de árbol para facilitar la navegación.
                    </p>
                    <div style="background: white; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #1e293b;">
                        📁 Papelería (categoría raíz)<br>
                        &nbsp;&nbsp;├─ 📂 Tarjetas (15)<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;└─ 📄 Tarjetas de Presentación (8)<br>
                        &nbsp;&nbsp;├─ 📂 Sobres (12)<br>
                        📁 Packaging (categoría raíz)
                    </div>
                    <p style="margin: 12px 0 0 0; font-size: 12px; color: #0c4a6e;">
                        <strong>Nota:</strong> Los números entre paréntesis indican la cantidad de productos en esa categoría.
                    </p>
                </div>
            ''')
        }),
        
        ('📝 DESCRIPCIONES', {
            'fields': ('short_description', 'description'),
            'description': mark_safe('''
                <div style="background: #fef3c7; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #f59e0b;">
                    <strong style="color: #92400e;">SEO Tips:</strong>
                    <ul style="margin: 8px 0;">
                        <li><strong>Descripción corta:</strong> Úsala para listados y meta description (máx 500 chars)</li>
                        <li><strong>Descripción completa:</strong> Detalla características, usos y beneficios</li>
                    </ul>
                </div>
            ''')
        }),
        
        ('🖼️ IMAGEN PRINCIPAL', {
            'fields': ('image', 'image_preview_large', 'image_info'),
            'description': mark_safe('''
                <div style="background: #f0fdf4; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #10b981;">
                    <strong style="color: #065f46;">📸 Recomendaciones:</strong>
                    <ul style="margin: 8px 0;">
                        <li><strong>Formato:</strong> PNG con fondo transparente (ideal)</li>
                        <li><strong>Tamaño:</strong> 1300x1300px (se redimensiona automáticamente)</li>
                        <li><strong>Composición:</strong> Producto centrado, sin distracciones</li>
                        <li><strong>Iluminación:</strong> Clara y uniforme</li>
                    </ul>
                </div>
            ''')
        }),
        
        ('🏷️ TAGS', {
            'fields': ('tag',),
            'description': mark_safe('''
                <div style="background: #fce7f3; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #ec4899;">
                    <strong style="color: #9f1239;">🏷️ Tags Sugeridos:</strong>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Económico</span>
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Premium</span>
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Packaging</span>
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Corporativo</span>
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Ecológico</span>
                        <span style="background: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #f9a8d4;">Personalizado</span>
                    </div>
                </div>
            ''')
        }),
        
        ('📊 ESTADÍSTICAS', {
            'fields': ('price_stats', 'discount_stats', 'product_stats'),
            'classes': ('collapse',),
        }),
        
        ('📅 METADATA', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'publish_products',
        'unpublish_products',
        'duplicate_product',
        'clear_product_cache'
    ]
    
    # ========================================================================
    # READONLY FIELDS
    # ========================================================================
    
    def quick_guide(self, obj):
        return ""
    quick_guide.short_description = ""
    
    def image_preview_large(self, obj):
        """Preview grande de imagen"""
        if obj.image:
            return format_html(
                '<div style="margin: 20px 0;">'
                '<div style="background: #f9fafb; padding: 20px; border-radius: 12px; display: inline-block;">'
                '<img src="{}" style="max-width: 600px; max-height: 600px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); display: block;" />'
                '</div>'
                '<div style="margin-top: 15px; display: flex; gap: 12px;">'
                '<a href="{}" target="_blank" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);">'
                '🔗 Ver original'
                '</a>'
                '<button type="button" onclick="navigator.clipboard.writeText(\'{}\'); this.innerText = \'✅ Copiada!\'; setTimeout(() => this.innerText = \'📋 Copiar URL\', 2000);" '
                'style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">'
                '📋 Copiar URL'
                '</button>'
                '</div>'
                '</div>',
                obj.image.url, obj.image.url, obj.image.url
            )
        return format_html(
            '<div style="padding: 60px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius: 12px; text-align: center; border: 3px dashed #9ca3af;">'
            '<div style="font-size: 64px; margin-bottom: 16px;">📷</div>'
            '<div style="color: #6b7280; font-size: 18px; font-weight: 600;">No hay imagen principal</div>'
            '</div>'
        )
    image_preview_large.short_description = 'Vista Previa'
    
    def image_info(self, obj):
        """Info detallada de imagen"""
        if obj.image:
            try:
                size_mb = obj.image.size / (1024 * 1024)
                size_kb = obj.image.size / 1024
                
                if size_mb > 2:
                    color = '#ef4444'
                    icon = '⚠️'
                    status = 'MUY GRANDE'
                elif size_mb > 1:
                    color = '#f59e0b'
                    icon = '⚡'
                    status = 'GRANDE'
                else:
                    color = '#10b981'
                    icon = '✅'
                    status = 'ÓPTIMO'
                
                return format_html(
                    '<div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 20px; border-radius: 10px; border-left: 5px solid {};">'
                    '<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">'
                    '<div style="font-size: 32px;">{}</div>'
                    '<div><div style="font-size: 16px; font-weight: 700; color: #065f46;">Info de Imagen</div>'
                    '<div style="font-size: 12px; color: #047857; font-weight: 600;">{}</div></div>'
                    '</div>'
                    '<table style="width: 100%; font-size: 13px;">'
                    '<tr><td style="padding: 8px 0; color: #065f46; font-weight: 600;">📊 Tamaño:</td>'
                    '<td style="padding: 8px 0; color: #047857;"><strong>{} MB</strong> ({} KB)</td></tr>'
                    '<tr><td style="padding: 8px 0; color: #065f46; font-weight: 600;">🔗 URL:</td>'
                    '<td style="padding: 8px 0;"><code style="background: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; word-break: break-all;">{}</code></td></tr>'
                    '</table>'
                    '</div>',
                    color, icon, status, round(size_mb, 2), round(size_kb, 0), obj.image.url
                )
            except:
                return 'Error al cargar'
        return 'Sin imagen'
    image_info.short_description = 'Info Detallada'
    
    def price_stats(self, obj):
        """Estadísticas de precios"""
        if obj.pk:
            prices = obj.product_base_prices.all()
            count = prices.count()
            
            if count > 0:
                price_values = list(prices.values_list('price', flat=True))
                min_price = float(min(price_values))
                max_price = float(max(price_values))
                
                return format_html(
                    '<div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 20px; border-radius: 10px;">'
                    '<h3 style="margin: 0 0 15px 0; color: #1e40af;">💰 Estadísticas de Precios</h3>'
                    '<table style="width: 100%; border-collapse: collapse;">'
                    '<tr><td style="padding: 8px 0; color: #1e40af; font-weight: 600;">📊 Total de precios:</td>'
                    '<td style="padding: 8px 0; color: #1e3a8a; font-weight: 700; font-size: 16px;">{}</td></tr>'
                    '<tr><td style="padding: 8px 0; color: #1e40af; font-weight: 600;">💵 Precio mínimo:</td>'
                    '<td style="padding: 8px 0; color: #1e3a8a; font-weight: 700; font-size: 16px;">${}</td></tr>'
                    '<tr><td style="padding: 8px 0; color: #1e40af; font-weight: 600;">💎 Precio máximo:</td>'
                    '<td style="padding: 8px 0; color: #1e3a8a; font-weight: 700; font-size: 16px;">${}</td></tr>'
                    '</table>'
                    '</div>',
                    count, round(min_price, 2), round(max_price, 2)
                )
            return format_html(
                '<div style="background: #fef3c7; padding: 20px; border-radius: 10px; border-left: 4px solid #f59e0b;">'
                '<strong style="color: #92400e;">⚠️ Sin precios configurados</strong>'
                '<p style="margin: 8px 0 0 0; color: #78350f;">Agrega al menos un precio en la tabla inferior</p>'
                '</div>'
            )
        return 'Guarda primero para ver estadísticas'
    price_stats.short_description = 'Estadísticas de Precios'
    
    def discount_stats(self, obj):
        """Estadísticas de descuentos"""
        if obj.pk:
            now = timezone.now()
            all_discounts = obj.product_base_discounts.all()
            active_discounts = all_discounts.filter(
                start_date__lte=now,
                expiration_date__gte=now
            ).count()
            
            total = all_discounts.count()
            
            if total > 0:
                color = '#10b981' if active_discounts > 0 else '#6b7280'
                return format_html(
                    '<div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 20px; border-radius: 10px;">'
                    '<h3 style="margin: 0 0 15px 0; color: #065f46;">🎁 Estadísticas de Descuentos</h3>'
                    '<table style="width: 100%;">'
                    '<tr><td style="padding: 8px 0; color: #065f46; font-weight: 600;">Total:</td>'
                    '<td style="padding: 8px 0; color: #047857; font-weight: 700;">{}</td></tr>'
                    '<tr><td style="padding: 8px 0; color: #065f46; font-weight: 600;">Activos ahora:</td>'
                    '<td style="padding: 8px 0;"><span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">{}</span></td></tr>'
                    '</table>'
                    '</div>',
                    total, color, active_discounts
                )
            return format_html(
                '<div style="background: #f3f4f6; padding: 20px; border-radius: 10px; text-align: center;">'
                '<div style="color: #6b7280;">Sin descuentos configurados</div>'
                '</div>'
            )
        return 'Guarda primero'
    discount_stats.short_description = 'Estadísticas de Descuentos'
    
    def product_stats(self, obj):
        """Estadísticas generales del producto"""
        if obj.pk:
            gallery_count = obj.product_base_images.count()
            tags_count = obj.tag.count()
            
            return format_html(
                '<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 10px;">'
                '<h3 style="margin: 0 0 15px 0; color: #92400e;">📊 Estadísticas Generales</h3>'
                '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">'
                '<div style="background: white; padding: 15px; border-radius: 8px;">'
                '<div style="font-size: 32px; color: #f59e0b; margin-bottom: 8px;">🖼️</div>'
                '<div style="font-size: 24px; font-weight: 700; color: #92400e;">{}</div>'
                '<div style="font-size: 12px; color: #78350f;">Imágenes en galería</div>'
                '</div>'
                '<div style="background: white; padding: 15px; border-radius: 8px;">'
                '<div style="font-size: 32px; color: #f59e0b; margin-bottom: 8px;">🏷️</div>'
                '<div style="font-size: 24px; font-weight: 700; color: #92400e;">{}</div>'
                '<div style="font-size: 12px; color: #78350f;">Tags asignados</div>'
                '</div>'
                '</div>'
                '</div>',
                gallery_count, tags_count
            )
        return 'Guarda primero'
    product_stats.short_description = 'Estadísticas del Producto'
    
    # ========================================================================
    # LIST DISPLAY METHODS
    # ========================================================================
    
    def id_badge(self, obj):
        """Badge de ID"""
        return format_html(
            '<span style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 6px 12px; border-radius: 12px; font-weight: 700; box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3); font-family: monospace;">#{}</span>',
            obj.id
        )
    id_badge.short_description = 'ID'
    id_badge.admin_order_field = 'id'
    
    def image_preview_list(self, obj):
        """Preview en lista"""
        if obj.image:
            return format_html(
                '<div style="position: relative; display: inline-block;">'
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #e5e7eb;" />'
                '<div style="position: absolute; bottom: 4px; right: 4px; background: rgba(139, 92, 246, 0.9); color: white; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: 600;">✓</div>'
                '</div>',
                obj.image.url
            )
        return format_html(
            '<div style="width: 80px; height: 80px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 2px dashed #9ca3af;">'
            '<span style="font-size: 32px;">📷</span></div>'
        )
    image_preview_list.short_description = 'Imagen'
    
    def slug_display(self, obj):
        """Slug con copy"""
        return format_html(
            '<code style="background: #f3f4f6; padding: 6px 10px; border-radius: 6px; font-size: 11px; cursor: pointer;" '
            'onclick="navigator.clipboard.writeText(\'{}\'); this.style.background=\'#8b5cf6\'; this.style.color=\'white\'; setTimeout(() => {{ this.style.background=\'#f3f4f6\'; this.style.color=\'#1f2937\'; }}, 1000);">{}</code>',
            obj.slug, obj.slug[:25] + '...' if len(obj.slug) > 25 else obj.slug
        )
    slug_display.short_description = 'Slug'
    slug_display.admin_order_field = 'slug'
    
    def category_badge(self, obj):
        """Badge de categoría"""
        if obj.category:
            return format_html(
                '<span style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; box-shadow: 0 2px 4px rgba(6, 182, 212, 0.3);">📂 {}</span>',
                obj.category.title
            )
        return '-'
    category_badge.short_description = 'Categoría'
    category_badge.admin_order_field = 'category'
    
    def price_range_display(self, obj):
        """Rango de precios"""
        prices = obj.product_base_prices.all()
        if prices:
            price_values = list(prices.values_list('price', flat=True))
            min_p = float(min(price_values))
            max_p = float(max(price_values))
            
            if min_p == max_p:
                return format_html(
                    '<div style="text-align: center;">'
                    '<div style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 700; display: inline-block;">${}</div>'
                    '</div>',
                    round(min_p, 2)
                )
            else:
                return format_html(
                    '<div style="text-align: center; font-size: 12px;">'
                    '<div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); color: white; padding: 6px 12px; border-radius: 12px; font-weight: 700; display: inline-block;">'
                    '${} - ${}'
                    '</div>'
                    '</div>',
                    round(min_p, 2), round(max_p, 2)
                )
        return format_html('<span style="color: #9ca3af;">Sin precios</span>')
    price_range_display.short_description = 'Rango Precio'
    
    def tags_display(self, obj):
        """Tags display con badges limpios"""
        tags = list(obj.tag.all()[:3])
        
        if not tags:
            return format_html('<span style="color: #9ca3af; font-size: 12px;">—</span>')
        
        # Construir HTML limpio para cada tag
        tags_html = ''
        for tag in tags:
            tags_html += format_html(
                '<span style="background: #e0e7ff; color: #4338ca; padding: 3px 8px; border-radius: 10px; font-size: 10px; margin-right: 4px; display: inline-block; margin-bottom: 2px;">{}</span>',
                tag.name
            )
        
        # Agregar contador si hay más de 3 tags
        total_tags = obj.tag.count()
        if total_tags > 3:
            tags_html += format_html(
                '<span style="color: #6b7280; font-size: 10px;">+{}</span>',
                total_tags - 3
            )
        
        return format_html('<div style="max-width: 150px;">{}</div>', mark_safe(tags_html))
    tags_display.short_description = 'Tags'
    
    def status_badge(self, obj):
        """Estado de publicación"""
        if obj.published:
            return format_html(
                '<span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);">'
                '<span style="width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>PUBLICADO</span>'
                '<style>@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}</style>'
            )
        return format_html(
            '<span style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; box-shadow: 0 2px 4px rgba(107, 114, 128, 0.3);">○ BORRADOR</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'published'
    
    def stats_badge(self, obj):
        """Badge de estadísticas rápidas"""
        prices_count = obj.product_base_prices.count()
        images_count = obj.product_base_images.count()
        
        return format_html(
            '<div style="font-size: 11px; text-align: center;">'
            '<div style="margin-bottom: 4px;">💰 {} precios</div>'
            '<div>🖼️ {} imgs</div>'
            '</div>',
            prices_count, images_count
        )
    stats_badge.short_description = 'Stats'
    
    # ========================================================================
    # ACCIONES
    # ========================================================================
    
    @admin.action(description='✅ Publicar productos')
    def publish_products(self, request, queryset):
        count = queryset.update(published=True)
        self.message_user(request, f"✅ {count} producto(s) publicado(s)")
    
    @admin.action(description='📝 Convertir a borrador')
    def unpublish_products(self, request, queryset):
        count = queryset.update(published=False)
        self.message_user(request, f"📝 {count} producto(s) convertido(s) a borrador")
    
    @admin.action(description='🔄 Duplicar producto')
    def duplicate_product(self, request, queryset):
        count = 0
        for product in queryset:
            product.pk = None
            product.key = None
            product.title = f"{product.title} (Copia)"
            product.slug = f"{product.slug}-copia"
            product.published = False
            product.save()
            count += 1
        self.message_user(request, f"🔄 {count} producto(s) duplicado(s)")
    
    @admin.action(description='🗑️ Limpiar caché de productos')
    def clear_product_cache(self, request, queryset):
        from core.product_base.api.services import ProductBaseService
        for product in queryset:
            ProductBaseService.invalidate_product_cache(product.id)
        self.message_user(request, f"🗑️ Caché limpiado para {queryset.count()} producto(s)")
    
    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Widget personalizado para tags"""
        if db_field.name == 'tag':
            autocomplete_url = '/api/tags/autocomplete'
            kwargs['widget'] = HashtagAutocompleteWidget(
                attrs={
                    'data-autocomplete-url': autocomplete_url,
                    'class': 'vTextField',
                    'placeholder': 'Ej: economico, premium, packaging'
                }
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Invalidar caché al guardar"""
        super().save_model(request, obj, form, change)
        if change:
            from core.product_base.api.services import ProductBaseService
            ProductBaseService.invalidate_product_cache(obj.id)
    
    class Media:
        css = {
            'all': ('admin/css/product-base-admin.css',)
        }
        js = ('admin/js/product-base-admin.js',)