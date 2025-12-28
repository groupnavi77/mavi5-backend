# admin.py - MEJORADO con títulos de sección y guías visuales

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Q
import json
from .models import Slider
from django.utils.safestring import mark_safe

class SliderAdminForm(forms.ModelForm):
    """Form con validaciones y auto-generación de slug"""
    
    # ✨ Título de sección para organizar el form
    section_title = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial='Información del Slider'
    )
    
    content_json = forms.CharField(
        label="Contenido JSON",
        widget=forms.Textarea(attrs={
            'rows': 20,
            'cols': 90,
            'style': 'font-family: Monaco, monospace; font-size: 13px;',
            'placeholder': 'Ingresa el contenido en formato JSON...'
        }),
        required=False,
        help_text='Contenido adicional en formato JSON'
    )
    
    class Meta:
        model = Slider
        fields = '__all__'
        widgets = {
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'image-upload-field'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Ej: New Season Women\'s Style',
                'style': 'width: 100%;'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'new-season-womens-style (se genera automático)',
                'style': 'width: 100%;'
            }),
            'section': forms.Select(attrs={
                'style': 'width: 100%;'
            }),
            'order': forms.NumberInput(attrs={
                'min': 0,
                'placeholder': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar JSON si existe
        if self.instance and self.instance.pk:
            self.initial['content_json'] = json.dumps(
                self.instance.content, 
                indent=4, 
                ensure_ascii=False
            )
        else:
            # JSON de ejemplo para nuevos sliders
            self.initial['content_json'] = json.dumps({
                "heading": "Título principal",
                "subheading": "Subtítulo opcional",
                "description": "Descripción del slide",
                "button": {
                    "text": "SHOP NOW",
                    "url": "/shop"
                },
                "styles": {
                    "background_color": "#f5f5f5",
                    "text_color": "#000000"
                }
            }, indent=4, ensure_ascii=False)
        
        # Configurar campo slug
        if 'slug' in self.fields:
            if not self.instance.pk:
                self.fields['slug'].required = False
                self.fields['slug'].help_text = "💡 Dejar vacío para generar automáticamente del título"
            else:
                self.fields['slug'].help_text = f"✅ Slug actual: <code>{self.instance.slug}</code>"
        
        # Mejorar help_text de otros campos
        if 'section' in self.fields:
            self.fields['section'].help_text = "📂 Selecciona dónde se mostrará este slider"
        
        if 'order' in self.fields:
            self.fields['order'].help_text = "🔢 Orden de visualización (menor número = primero)"
        
        if 'is_active' in self.fields:
            self.fields['is_active'].help_text = "✅ Activar/Desactivar slider"
        
        if 'start_date' in self.fields:
            self.fields['start_date'].help_text = "📅 Fecha desde la cual estará activo (opcional)"
        
        if 'end_date' in self.fields:
            self.fields['end_date'].help_text = "🏁 Fecha hasta la cual estará activo (opcional)"
    
    def clean_image(self):
        """Validar tamaño de imagen"""
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('⚠️ La imagen no debe superar los 5MB')
        return image
    
    def clean_content_json(self):
        """Validar y parsear JSON"""
        content_json = self.cleaned_data.get('content_json', '{}')
        if not content_json.strip():
            return {}
        try:
            parsed = json.loads(content_json)
            return parsed
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'❌ JSON inválido: {str(e)}')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.content = self.cleaned_data.get('content_json', {})
        
        if commit:
            instance.save()
        return instance


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    form = SliderAdminForm
    
    # Mostrar ID y SLUG en el listado
    list_display = [
        'id_badge',
        'title',
        'slug_display',
        'section_badge',
        'section_slug_badge',  # ✨ NUEVO: Slug de la sección
        'image_preview_list',
        'order',
        'status_badge',
        'updated_at'
    ]
    
    list_display_links = ['title']
    list_filter = ['section', 'is_active', 'created_at', 'updated_at']
    search_fields = ['id', 'title', 'slug', 'content']
    list_editable = ['order']
    readonly_fields = ['id', 'image_preview_large', 'image_info', 'created_at', 'updated_at', 'quick_guide']
    prepopulated_fields = {'slug': ('title',)}
    
    # ✨ FIELDSETS MEJORADOS CON TÍTULOS Y GUÍAS
    fieldsets = (
        ('📌 INFORMACIÓN BÁSICA', {
            'fields': ('quick_guide',),
            'description': mark_safe('''
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin: 15px 0;">
                    <h2 style="margin: 0 0 15px 0; color: white;">🎯 Guía Rápida de Uso</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                            <strong style="display: block; margin-bottom: 8px;">🏠 Para Slider Principal:</strong>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Sección: <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">home_hero</code></li>
                                <li>Orden: 0, 1, 2, etc.</li>
                                <li>Imagen: Grande, producto centrado</li>
                            </ul>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                            <strong style="display: block; margin-bottom: 8px;">🎁 Para Banners Laterales:</strong>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Sección: <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">home_deals</code></li>
                                <li>Orden: 0, 1</li>
                                <li>Imagen: Pequeña, decorativa</li>
                            </ul>
                        </div>
                    </div>
                </div>
            ''')
        }),
        
        ('🔢 IDENTIFICACIÓN', {
            'fields': ('id', 'title', 'slug'),
            'description': mark_safe('''
                <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #1e40af;">💡 Tip:</strong> El título es solo para tu referencia en el admin. El slug se usa para URLs amigables.
                </div>
            ''')
        }),
        
        ('📂 UBICACIÓN Y VISUALIZACIÓN', {
            'fields': ('section', 'order', 'is_active'),
            'description': mark_safe('''
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #065f46;">📍 Secciones disponibles y sus slugs para API:</strong>
                    <table style="margin-top: 10px; width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #d1fae5;">
                                <th style="padding: 8px; text-align: left; border: 1px solid #a7f3d0;">Nombre</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #a7f3d0;">Slug (API)</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #a7f3d0;">Uso</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #d1fae5;">Home - Hero Banner</td>
                                <td style="padding: 8px; border: 1px solid #d1fae5;"><code style="background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 3px;">home_hero</code></td>
                                <td style="padding: 8px; border: 1px solid #d1fae5; font-size: 12px;">Slider principal del home (carousel)</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #d1fae5;">Home - Ofertas</td>
                                <td style="padding: 8px; border: 1px solid #d1fae5;"><code style="background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 3px;">home_deals</code></td>
                                <td style="padding: 8px; border: 1px solid #d1fae5; font-size: 12px;">Banners de ofertas laterales</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #d1fae5;">Home - Categorías</td>
                                <td style="padding: 8px; border: 1px solid #d1fae5;"><code style="background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 3px;">home_categories</code></td>
                                <td style="padding: 8px; border: 1px solid #d1fae5; font-size: 12px;">Categorías destacadas</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #d1fae5;">Producto - Banner</td>
                                <td style="padding: 8px; border: 1px solid #d1fae5;"><code style="background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 3px;">product_banner</code></td>
                                <td style="padding: 8px; border: 1px solid #d1fae5; font-size: 12px;">Banner de página de producto</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #d1fae5;">Categoría - Banner</td>
                                <td style="padding: 8px; border: 1px solid #d1fae5;"><code style="background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 3px;">category_banner</code></td>
                                <td style="padding: 8px; border: 1px solid #d1fae5; font-size: 12px;">Banner de categoría</td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="background: #dbeafe; padding: 10px; border-radius: 6px; margin-top: 10px;">
                        <strong style="color: #1e40af;">💡 Ejemplo de uso en API:</strong>
                        <code style="display: block; margin-top: 6px; background: #1f2937; color: #10b981; padding: 8px; border-radius: 4px; font-size: 12px;">
                            GET /api/sliders/section/home_hero
                        </code>
                    </div>
                </div>
            ''')
        }),
        
        ('🖼️ IMAGEN PRINCIPAL', {
            'fields': ('image', 'image_preview_large', 'image_info'),
            'description': mark_safe('''
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #92400e;">📸 Recomendaciones de imagen:</strong>
                    <ul style="margin-top: 8px;">
                        <li><strong>Tamaño:</strong> Mínimo 1000x1000px, máximo 2000x2000px</li>
                        <li><strong>Formato:</strong> PNG con fondo transparente (recomendado) o JPG</li>
                        <li><strong>Peso:</strong> Máximo 5MB, idealmente 500KB-1MB</li>
                        <li><strong>Contenido:</strong> Centrar el producto/persona principal</li>
                    </ul>
                </div>
            ''')
        }),
        
        ('⏰ PROGRAMACIÓN (Opcional)', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div style="background: #fce7f3; border-left: 4px solid #ec4899; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #9f1239;">⏰ Programación automática:</strong>
                    <p style="margin: 8px 0 0 0;">
                        Usa estas fechas si quieres que el slider se active/desactive automáticamente.
                        Si las dejas vacías, el slider estará siempre activo (mientras is_active=True).
                    </p>
                </div>
            ''')
        }),
        
        ('📝 CONTENIDO DEL SLIDER (JSON)', {
            'fields': ('content_json',),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #111827;">📋 Estructura del JSON</h3>
                    
                    <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                        <h4 style="margin-top: 0; color: #3b82f6;">🎯 Slider Principal (home_hero)</h4>
                        <pre style="background: #1f2937; color: #10b981; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 13px;">{
    "subheading": "FRESH AND TASTY",
    "heading": "New Season Women's Style",
    "description": "Discover the beauty of fashion living",
    "button": {
        "text": "SHOP NOW",
        "url": "/shop/breadcrumb-img"
    },
    "styles": {
        "background_color": "#f5f5f5",
        "text_color": "#000000"
    }
}</pre>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 6px;">
                        <h4 style="margin-top: 0; color: #ef4444;">🎁 Banner Lateral (home_deals)</h4>
                        <pre style="background: #1f2937; color: #10b981; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 13px;">{
    "heading": "Dive into Savings\\nOn Swimwear",
    "badge": {
        "text": "SAVE $10",
        "color": "#dc2626"
    },
    "price": {
        "label": "Starting at",
        "amount": "$59.99"
    },
    "button": {
        "url": "/shop/swimwear"
    },
    "styles": {
        "background_color": "#f5f5f5"
    }
}</pre>
                    </div>
                    
                    <div style="background: #dbeafe; padding: 12px; border-radius: 6px; margin-top: 15px;">
                        <strong style="color: #1e40af;">💡 Campos disponibles:</strong>
                        <ul style="margin: 8px 0 0 0; columns: 2;">
                            <li><code>heading</code> - Título principal</li>
                            <li><code>subheading</code> - Subtítulo</li>
                            <li><code>description</code> - Descripción</li>
                            <li><code>button</code> - Botón CTA</li>
                            <li><code>badge</code> - Etiqueta (ej: SAVE $10)</li>
                            <li><code>price</code> - Precio/Oferta</li>
                            <li><code>styles</code> - Colores personalizados</li>
                        </ul>
                    </div>
                </div>
            ''')
        }),
        
        ('📊 INFORMACIÓN DEL SISTEMA', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # ✨ Campo de guía rápida (solo visual)
    def quick_guide(self, obj):
        return ""
    quick_guide.short_description = ""
    
    # ✨ ID con badge
    def id_badge(self, obj):
        if obj.id:
            return format_html(
                '<span style="background: #3b82f6; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; font-family: monospace;">#{}</span>',
                obj.id
            )
        return '-'
    id_badge.short_description = 'ID'
    id_badge.admin_order_field = 'id'
    
    # ✨ Slug display
    def slug_display(self, obj):
        if obj.slug:
            return format_html(
                '<code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #1f2937; cursor: pointer;" title="Click para copiar" onclick="navigator.clipboard.writeText(\'{}\'); alert(\'✅ Slug copiado al portapapeles!\');">{}</code>',
                obj.slug,
                obj.slug if len(obj.slug) <= 30 else obj.slug[:27] + '...'
            )
        return '-'
    slug_display.short_description = 'Slug'
    slug_display.admin_order_field = 'slug'
    
    def section_badge(self, obj):
        colors = {
            'home_hero': '#3b82f6',
            'home_deals': '#ef4444',
            'home_categories': '#8b5cf6',
            'product_banner': '#10b981',
            'category_banner': '#f59e0b',
            'checkout_promo': '#ec4899',
            'blog_featured': '#6366f1',
            'seasonal': '#f97316',
            'footer_promo': '#14b8a6',
            'custom': '#6b7280',
        }
        color = colors.get(obj.section, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">{}</span>',
            color,
            obj.get_section_display()
        )
    section_badge.short_description = 'Sección'
    section_badge.admin_order_field = 'section'
    
    # ✨ NUEVO: Mostrar slug de la sección
    def section_slug_badge(self, obj):
        """Muestra el slug de la sección para guía rápida de API"""
        return format_html(
            '<code style="background: #1f2937; color: #10b981; padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; display: inline-block;" title="Click para copiar - Usar en API: /api/sliders/section/{}" onclick="navigator.clipboard.writeText(\'{}\'); alert(\'✅ Slug de sección copiado: {}\');">{}</code>',
            obj.section,
            obj.section,
            obj.section,
            obj.section
        )
    section_slug_badge.short_description = 'Slug Sección (API)'
    section_slug_badge.admin_order_field = 'section'
    
    def image_preview_list(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">⚠️ Sin imagen</span>')
    image_preview_list.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '''
                <div style="margin: 10px 0;">
                    <img src="{}" style="max-width: 600px; max-height: 400px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />
                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                        <a href="{}" target="_blank" style="color: white; background: #3b82f6; text-decoration: none; padding: 10px 16px; border-radius: 6px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">
                            🔗 Ver imagen completa
                        </a>
                        <button type="button" onclick="navigator.clipboard.writeText('{}'); alert('✅ URL copiada!');" style="background: #10b981; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">
                            📋 Copiar URL
                        </button>
                    </div>
                </div>
                ''',
                obj.image.url,
                obj.image.url,
                obj.image.url
            )
        return format_html('<p style="color: #9ca3af; padding: 20px; background: #f9fafb; border-radius: 6px; text-align: center;">📷 No hay imagen subida</p>')
    image_preview_large.short_description = 'Vista previa de la imagen'
    
    def image_info(self, obj):
        if obj.image:
            try:
                size_mb = obj.image.size / (1024 * 1024)
                size_kb = obj.image.size / 1024
                filename = obj.image.name.split('/')[-1]
                
                # Color según tamaño
                if size_mb > 2:
                    color = '#ef4444'  # Rojo - muy grande
                    icon = '⚠️'
                elif size_mb > 1:
                    color = '#f59e0b'  # Naranja - grande
                    icon = '⚡'
                else:
                    color = '#10b981'  # Verde - óptimo
                    icon = '✅'
                
                return format_html(
                    '''
                    <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 4px solid {};">
                        <p style="margin: 0; font-size: 14px; font-weight: 600; color: #065f46; margin-bottom: 10px;">
                            {} Información del archivo
                        </p>
                        <table style="width: 100%; font-size: 13px;">
                            <tr>
                                <td style="padding: 4px 0; color: #065f46;"><strong>📁 Archivo:</strong></td>
                                <td style="padding: 4px 0; color: #047857;">{}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #065f46;"><strong>📊 Tamaño:</strong></td>
                                <td style="padding: 4px 0; color: #047857;">{:.2f} MB ({:.0f} KB)</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #065f46; vertical-align: top;"><strong>🔗 URL:</strong></td>
                                <td style="padding: 4px 0;">
                                    <code style="background: white; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 2px; font-size: 11px; word-break: break-all; color: #047857;">{}</code>
                                </td>
                            </tr>
                        </table>
                    </div>
                    ''',
                    color,
                    icon,
                    filename,
                    size_mb,
                    size_kb,
                    obj.image.url
                )
            except Exception as e:
                return format_html('<p style="color: #ef4444; background: #fef2f2; padding: 10px; border-radius: 6px;">❌ Error: {}</p>', str(e))
        return format_html('<p style="color: #9ca3af; padding: 15px; background: #f9fafb; border-radius: 6px; text-align: center;">📷 No hay información disponible</p>')
    image_info.short_description = 'Información detallada'
    
    def status_badge(self, obj):
        if obj.is_currently_active():
            return format_html(
                '<span style="background: #10b981; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">● ACTIVO</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">⏰ PROGRAMADO</span>'
            )
        else:
            return format_html(
                '<span style="background: #6b7280; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">○ INACTIVO</span>'
            )
    status_badge.short_description = 'Estado'
    
    # Acciones personalizadas
    actions = ['duplicate_slider', 'activate_sliders', 'deactivate_sliders']
    
    def duplicate_slider(self, request, queryset):
        duplicated = 0
        for slider in queryset:
            original_image = slider.image
            slider.pk = None
            slider.id = None
            slider.title = f"{slider.title} (Copia)"
            slider.slug = ''
            slider.is_active = False
            slider.image = original_image
            slider.save()
            duplicated += 1
        self.message_user(request, f"✅ {duplicated} slider(s) duplicado(s) exitosamente")
    duplicate_slider.short_description = "🔄 Duplicar slider(s) seleccionado(s)"
    
    def activate_sliders(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"✅ {count} slider(s) activado(s) exitosamente")
    activate_sliders.short_description = "✅ Activar slider(s) seleccionado(s)"
    
    def deactivate_sliders(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"⏸️ {count} slider(s) desactivado(s) exitosamente")
    deactivate_sliders.short_description = "⏸️ Desactivar slider(s) seleccionado(s)"
    
    # ✨ Personalización adicional
    def get_form(self, request, obj=None, **kwargs):
        """Personalizar el formulario según el contexto"""
        form = super().get_form(request, obj, **kwargs)
        
        # Agregar clase CSS personalizada
        form.base_fields['content_json'].widget.attrs['class'] = 'json-editor'
        
        return form
    
    class Media:
        css = {
            'all': ('admin/css/slider_admin.css',)
        }
        js = ('admin/js/slider_admin.js',)