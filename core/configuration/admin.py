# core/configuration/admin.py - ADMIN ULTRA MEJORADO COMPLETO

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from mptt.admin import DraggableMPTTAdmin
import json

from .models import Slider, Menu, Page


# ============================================================================
# SLIDER ADMIN (ULTRA MEJORADO CON section_slug_badge)
# ============================================================================

class SliderAdminForm(forms.ModelForm):
    """Form con validaciones avanzadas y auto-generación de slug"""
    
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
                'placeholder': 'Ej: Banner Navidad 2024 (solo para admin)',
                'style': 'width: 100%; font-size: 14px;',
                'class': 'vTextField'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'banner-navidad-2024 (se genera automático)',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'section': forms.Select(attrs={
                'style': 'width: 100%;'
            }),
            'order': forms.NumberInput(attrs={
                'min': 0,
                'placeholder': '0',
                'style': 'width: 100px;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar JSON si existe
        if self.instance and self.instance.pk:
            self.initial['content_json'] = json.dumps(
                self.instance.content, indent=4, ensure_ascii=False
            )
        else:
            # JSON de ejemplo
            self.initial['content_json'] = json.dumps({
                "subheading": "FRESH AND TASTY",
                "heading": "New Season Women's Style",
                "description": "Discover the beauty of fashion living",
                "button": {
                    "text": "SHOP NOW",
                    "url": "/shop"
                },
                "styles": {
                    "background_color": "#f5f5f5",
                    "text_color": "#000000"
                }
            }, indent=4, ensure_ascii=False)
        
        # Configurar campos
        if 'slug' in self.fields:
            if not self.instance.pk:
                self.fields['slug'].required = False
                self.fields['slug'].help_text = "💡 Dejar vacío para generar automáticamente"
        
        if 'section' in self.fields:
            self.fields['section'].help_text = "📂 Sección donde se mostrará (ver tabla de slugs)"
        
        if 'order' in self.fields:
            self.fields['order'].help_text = "🔢 Orden (0 = primero)"
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('⚠️ Máximo 5MB')
        return image
    
    def clean_content_json(self):
        content_json = self.cleaned_data.get('content_json', '{}')
        if not content_json.strip():
            return {}
        try:
            return json.loads(content_json)
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
    """Admin ultra mejorado para sliders"""
    
    form = SliderAdminForm
    
    list_display = [
        'id_badge',
        'title',
        'slug_display',
        'section_badge',
        'section_slug_badge',  # ✨ NUEVO
        'image_preview_list',
        'order',
        'status_badge',
        'updated_at'
    ]
    
    list_display_links = ['title']
    list_filter = ['section', 'is_active', 'created_at']
    search_fields = ['id', 'title', 'slug']
    list_editable = ['order']
    readonly_fields = ['id', 'image_preview_large', 'image_info', 'created_at', 'updated_at', 'quick_guide', 'api_usage_guide']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('🎯 GUÍA RÁPIDA', {
            'fields': ('quick_guide',),
        }),
        ('🔢 IDENTIFICACIÓN', {
            'fields': ('id', 'title', 'slug'),
        }),
        ('📂 UBICACIÓN', {
            'fields': ('section', 'order', 'is_active', 'api_usage_guide'),
        }),
        ('🖼️ IMAGEN', {
            'fields': ('image', 'image_preview_large', 'image_info'),
        }),
        ('📝 CONTENIDO JSON', {
            'fields': ('content_json',),
            'classes': ('collapse',),
        }),
        ('⏰ PROGRAMACIÓN', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
        }),
        ('📊 METADATA', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['duplicate_slider', 'activate_sliders', 'deactivate_sliders', 'move_to_home_hero', 'move_to_home_deals']
    
    # Readonly fields
    def quick_guide(self, obj):
        return mark_safe('''
            <div style="background: linear-gradient(135deg, #f97316 0%, #dc2626 100%); color: white; padding: 25px; border-radius: 12px;">
                <h2 style="margin: 0 0 20px 0;">🎯 Guía Rápida</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                        <h3>1️⃣ Info Básica</h3>
                        <ul>
                            <li>Título para admin</li>
                            <li>Slug auto-generado</li>
                        </ul>
                    </div>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                        <h3>2️⃣ Ubicación</h3>
                        <ul>
                            <li>Sección donde va</li>
                            <li>Orden: 0 = primero</li>
                        </ul>
                    </div>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                        <h3>3️⃣ Imagen</h3>
                        <ul>
                            <li>PNG transparente</li>
                            <li>1500x1500px ideal</li>
                            <li>Máx 5MB</li>
                        </ul>
                    </div>
                </div>
            </div>
        ''')
    quick_guide.short_description = ""
    
    def api_usage_guide(self, obj):
        if obj.pk:
            api_url = f'/api/configuration/sliders/section/{obj.section}'
            return format_html(
                '<div style="background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; color: white;">'
                '<h3 style="margin: 0 0 15px 0;">🔗 Uso en API</h3>'
                '<div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 6px; margin-bottom: 10px;">'
                '<strong>Endpoint:</strong><br>'
                '<code style="background: rgba(0,0,0,0.3); color: #fbbf24; padding: 8px 12px; border-radius: 4px; display: block; margin-top: 6px;">{}</code>'
                '</div>'
                '<div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 6px;">'
                '<strong>JavaScript:</strong><br>'
                '<pre style="background: rgba(0,0,0,0.3); color: #a3e635; padding: 10px; border-radius: 4px; margin-top: 6px; font-size: 12px; overflow-x: auto;">fetch(\'{}\').then(r => r.json())</pre>'
                '</div>'
                '</div>',
                api_url, api_url
            )
        return "Guarda primero"
    api_usage_guide.short_description = "Guía API"
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<div style="margin: 20px 0;">'
                '<img src="{}" style="max-width: 700px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);" />'
                '<div style="margin-top: 15px;">'
                '<a href="{}" target="_blank" style="background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; margin-right: 10px;">🔗 Ver completa</a>'
                '<button type="button" onclick="navigator.clipboard.writeText(\'{}\'); alert(\'✅ Copiada!\');" style="background: #10b981; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;">📋 Copiar URL</button>'
                '</div>'
                '</div>',
                obj.image.url, obj.image.url, obj.image.url
            )
        return '<div style="padding: 60px; background: #f3f4f6; border-radius: 10px; text-align: center; border: 3px dashed #9ca3af;"><div style="font-size: 64px;">📷</div><div style="color: #6b7280; font-size: 18px; margin-top: 10px;">No hay imagen</div></div>'
    image_preview_large.short_description = 'Vista Previa'
    
    def image_info(self, obj):
        if obj.image:
            try:
                size_mb = obj.image.size / (1024 * 1024)
                color = '#10b981' if size_mb < 1 else '#f59e0b' if size_mb < 2 else '#ef4444'
                icon = '✅' if size_mb < 1 else '⚡' if size_mb < 2 else '⚠️'
                
                return format_html(
                    '<div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 5px solid {};">'
                    '<div style="font-size: 32px; margin-bottom: 10px;">{}</div>'
                    '<strong>Tamaño:</strong> {:.2f} MB<br>'
                    '<strong>URL:</strong> <code style="background: white; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 6px; font-size: 11px; word-break: break-all;">{}</code>'
                    '</div>',
                    color, icon, size_mb, obj.image.url
                )
            except:
                return 'Error al cargar info'
        return 'Sin imagen'
    image_info.short_description = 'Info Detallada'
    
    # List display methods
    def id_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 6px 12px; border-radius: 12px; font-weight: 700; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);">#{}</span>',
            obj.id
        )
    id_badge.short_description = 'ID'
    
    def slug_display(self, obj):
        return format_html(
            '<code style="background: #f3f4f6; padding: 6px 10px; border-radius: 6px; font-size: 11px; cursor: pointer;" '
            'onclick="navigator.clipboard.writeText(\'{}\'); this.style.background=\'#10b981\'; this.style.color=\'white\'; setTimeout(() => {{ this.style.background=\'#f3f4f6\'; this.style.color=\'#1f2937\'; }}, 1000);">{}</code>',
            obj.slug, obj.slug[:30] + '...' if len(obj.slug) > 30 else obj.slug
        )
    slug_display.short_description = 'Slug'
    
    def section_badge(self, obj):
        colors = {
            'home_hero': '#3b82f6', 'home_deals': '#ef4444', 'home_categories': '#8b5cf6',
            'product_banner': '#10b981', 'category_banner': '#f59e0b',
        }
        icons = {
            'home_hero': '🏠', 'home_deals': '🎁', 'home_categories': '📂',
            'product_banner': '🛍️', 'category_banner': '🏷️',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{} {}</span>',
            colors.get(obj.section, '#6b7280'),
            icons.get(obj.section, '📌'),
            obj.get_section_display()
        )
    section_badge.short_description = 'Sección'
    
    def section_slug_badge(self, obj):
        """✨ NUEVO: Badge con slug de sección para API"""
        return format_html(
            '<code style="background: #1f2937; color: #10b981; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;" '
            'title="Click para copiar" '
            'onmouseover="this.style.background=\'#374151\'" '
            'onmouseout="this.style.background=\'#1f2937\'" '
            'onclick="navigator.clipboard.writeText(\'{}\'); this.style.background=\'#10b981\'; setTimeout(() => this.style.background=\'#1f2937\', 1000); alert(\'✅ Copiado: {}\');">{}</code>',
            obj.section, obj.section, obj.section
        )
    section_slug_badge.short_description = 'Slug API'
    
    def image_preview_list(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #e5e7eb;" />',
                obj.image.url
            )
        return format_html(
            '<div style="width: 100px; height: 60px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 2px dashed #9ca3af;">'
            '<span style="font-size: 24px;">📷</span></div>'
        )
    image_preview_list.short_description = 'Preview'
    
    def status_badge(self, obj):
        if obj.is_currently_active():
            return format_html(
                '<span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);">'
                '<span style="display: inline-block; width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>ACTIVO</span>'
                '<style>@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}</style>'
            )
        elif obj.is_active:
            return format_html('<span style="background: #f59e0b; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600;">⏰ PROGRAMADO</span>')
        return format_html('<span style="background: #6b7280; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600;">○ INACTIVO</span>')
    status_badge.short_description = 'Estado'
    
    # Actions
    @admin.action(description='🔄 Duplicar sliders')
    def duplicate_slider(self, request, queryset):
        count = 0
        for slider in queryset:
            slider.pk = None
            slider.title = f"{slider.title} (Copia)"
            slider.slug = ''
            slider.is_active = False
            slider.save()
            count += 1
        self.message_user(request, f"✅ {count} duplicado(s)")
    
    @admin.action(description='✅ Activar')
    def activate_sliders(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"✅ {count} activado(s)")
    
    @admin.action(description='⏸️ Desactivar')
    def deactivate_sliders(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"⏸️ {count} desactivado(s)")
    
    @admin.action(description='🏠 Mover a Home Hero')
    def move_to_home_hero(self, request, queryset):
        count = queryset.update(section='home_hero')
        self.message_user(request, f"🏠 {count} movido(s)")
    
    @admin.action(description='🎁 Mover a Home Deals')
    def move_to_home_deals(self, request, queryset):
        count = queryset.update(section='home_deals')
        self.message_user(request, f"🎁 {count} movido(s)")

# ============================================================================
# MENU ADMIN (ULTRA MEJORADO)
# ============================================================================

class MenuAdminForm(forms.ModelForm):
    """Form con validaciones avanzadas y ayudas visuales"""
    
    class Meta:
        model = Menu
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ej: Shop Now, Categorías, Ayuda',
                'style': 'width: 100%; font-size: 14px;',
                'class': 'vTextField'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'shop-now (se genera automáticamente)',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'url': forms.TextInput(attrs={
                'placeholder': 'Ej: /shop, /about, https://external.com',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'icon': forms.TextInput(attrs={
                'placeholder': 'Ej: fa-home, bi-cart, lucide-menu',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descripción que aparece al hacer hover o en mega menús',
                'style': 'width: 100%;'
            }),
            'css_classes': forms.TextInput(attrs={
                'placeholder': 'Ej: btn-primary highlight featured',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'order': forms.NumberInput(attrs={
                'min': 0,
                'style': 'width: 100px;'
            }),
            'mega_menu_columns': forms.NumberInput(attrs={
                'min': 1,
                'max': 6,
                'style': 'width: 100px;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Slug auto-generado
        if 'slug' in self.fields:
            if not self.instance.pk:
                self.fields['slug'].required = False
                self.fields['slug'].help_text = "💡 Dejar vacío para generar del nombre"
        
        # Help texts mejorados
        if 'menu_type' in self.fields:
            self.fields['menu_type'].help_text = "📍 Ubicación donde se mostrará"
        
        if 'link_type' in self.fields:
            self.fields['link_type'].help_text = "🔗 Tipo de destino del enlace"
        
        if 'parent' in self.fields:
            self.fields['parent'].help_text = "📂 Menú padre (dejar vacío para nivel raíz)"
        
        if 'category' in self.fields:
            self.fields['category'].help_text = "🏷️ Solo si 'Tipo de Enlace' es 'Categoría'"
        
        if 'page' in self.fields:
            self.fields['page'].help_text = "📄 Solo si 'Tipo de Enlace' es 'Página'"
    
    def clean(self):
        cleaned_data = super().clean()
        link_type = cleaned_data.get('link_type')
        url = cleaned_data.get('url')
        category = cleaned_data.get('category')
        page = cleaned_data.get('page')
        
        # Validaciones según link_type
        if link_type == 'url' and not url:
            raise ValidationError({
                'url': '⚠️ Se requiere una URL para el tipo "URL Personalizada"'
            })
        
        if link_type == 'category' and not category:
            raise ValidationError({
                'category': '⚠️ Selecciona una categoría para el tipo "Categoría"'
            })
        
        if link_type == 'page' and not page:
            raise ValidationError({
                'page': '⚠️ Selecciona una página para el tipo "Página"'
            })
        
        if link_type == 'external' and not url:
            raise ValidationError({
                'url': '⚠️ Se requiere una URL completa para enlaces externos'
            })
        
        # Validar URL externa
        if link_type == 'external' and url:
            if not url.startswith(('http://', 'https://')):
                raise ValidationError({
                    'url': '⚠️ Los enlaces externos deben comenzar con http:// o https://'
                })
        
        return cleaned_data


@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    """Admin ultra mejorado para menús con drag & drop y guías visuales"""
    
    form = MenuAdminForm
    mptt_level_indent = 30
    
    list_display = [
        'tree_actions',
        'indented_title',
        'menu_type_badge',
        'link_type_badge',
        'url_display',
        'icon_display',
        'order',
        'status_badge',
        'updated_at',
    ]
    
    list_display_links = ['indented_title']
    list_filter = ['menu_type', 'link_type', 'is_active', 'is_featured']
    search_fields = ['name', 'slug', 'url', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'preview_url_box', 
        'image_preview_large',
        'quick_guide',
        'hierarchy_info'
    ]
    
    fieldsets = (
        ('🎯 GUÍA RÁPIDA', {
            'fields': ('quick_guide',),
            'description': mark_safe('''
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0;">
                    <h2 style="margin: 0 0 20px 0; color: white; font-size: 22px;">🎯 Guía Rápida: Crear un Menú</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        
                        <!-- Paso 1 -->
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; border-left: 4px solid #fbbf24;">
                            <div style="font-size: 32px; margin-bottom: 10px;">1️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">Información Básica</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Nombre:</strong> Texto visible (ej: "Shop Now")</li>
                                <li><strong>Slug:</strong> Déjalo vacío (se genera solo)</li>
                                <li><strong>Padre:</strong> Vacío = menú raíz</li>
                            </ul>
                        </div>
                        
                        <!-- Paso 2 -->
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;">
                            <div style="font-size: 32px; margin-bottom: 10px;">2️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">Tipo y Ubicación</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Tipo de Menú:</strong> ¿Dónde va?
                                    <ul style="margin-top: 5px;">
                                        <li>Header = Menú superior</li>
                                        <li>Footer = Pie de página</li>
                                        <li>Mobile = Hamburger menu</li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                        
                        <!-- Paso 3 -->
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;">
                            <div style="font-size: 32px; margin-bottom: 10px;">3️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">Configurar Enlace</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Tipo de Enlace:</strong>
                                    <ul style="margin-top: 5px;">
                                        <li><strong>URL:</strong> /shop, /about</li>
                                        <li><strong>Categoría:</strong> Selecciona del dropdown</li>
                                        <li><strong>Página:</strong> Privacidad, Términos, etc</li>
                                        <li><strong>Externo:</strong> https://ejemplo.com</li>
                                        <li><strong>Mega Menú:</strong> Solo contenedor</li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                        
                        <!-- Paso 4 -->
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; border-left: 4px solid #ec4899;">
                            <div style="font-size: 32px; margin-bottom: 10px;">4️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">Personalizar (Opcional)</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Icono:</strong> fa-home, bi-cart</li>
                                <li><strong>Descripción:</strong> Texto hover</li>
                                <li><strong>Orden:</strong> 0 = primero</li>
                                <li><strong>Destacado:</strong> Para estilos especiales</li>
                            </ul>
                        </div>
                        
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <strong style="font-size: 16px;">💡 Ejemplo Completo:</strong>
                        <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 6px; margin-top: 10px; font-family: monospace; font-size: 13px;">
                            Nombre: "Categorías"<br>
                            Tipo de Menú: Header<br>
                            Tipo de Enlace: URL<br>
                            URL: /categorias<br>
                            Icono: fa-list<br>
                            Orden: 1
                        </div>
                    </div>
                </div>
            ''')
        }),
        
        ('📋 INFORMACIÓN BÁSICA', {
            'fields': ('name', 'slug', 'parent', 'hierarchy_info'),
        }),
        
        ('🔗 TIPO Y ENLACE', {
            'fields': ('menu_type', 'link_type', 'url', 'category', 'page', 'preview_url_box'),
            'description': mark_safe('''
                <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; border-radius: 6px;">
                    <strong style="color: #1e40af; font-size: 15px;">💡 ¿Qué Tipo de Enlace usar?</strong>
                    <table style="margin-top: 12px; width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #bfdbfe;">
                                <th style="padding: 10px; text-align: left; border: 1px solid #93c5fd;">Tipo</th>
                                <th style="padding: 10px; text-align: left; border: 1px solid #93c5fd;">Cuándo Usar</th>
                                <th style="padding: 10px; text-align: left; border: 1px solid #93c5fd;">Ejemplo</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>URL Personalizada</code></td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Enlaces internos estáticos</td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>/shop</code>, <code>/about</code></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>Categoría</code></td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Enlazar a categoría de productos</td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Electrónica, Ropa, Hogar</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>Página</code></td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Páginas estáticas del CMS</td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Privacidad, Términos, Ayuda</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>Enlace Externo</code></td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">URLs externas completas</td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>https://blog.ejemplo.com</code></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #dbeafe;"><code>Mega Menú</code></td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">Contenedor para sub-menús</td>
                                <td style="padding: 10px; border: 1px solid #dbeafe;">No navega, solo muestra hijos</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            ''')
        }),
        
        ('🎨 PERSONALIZACIÓN VISUAL', {
            'fields': ('icon', 'image', 'image_preview_large', 'description'),
            'classes': ('collapse',),
        }),
        
        ('⚙️ CONFIGURACIÓN', {
            'fields': (
                'order', 
                'is_active', 
                'is_featured', 
                'open_in_new_tab', 
                'mega_menu_columns'
            ),
        }),
        
        ('🔧 AVANZADO', {
            'fields': ('css_classes', 'attributes'),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; border-radius: 6px;">
                    <strong style="color: #92400e;">⚠️ Sección Avanzada</strong>
                    <p style="margin: 8px 0 0 0; color: #78350f;">
                        Estos campos son opcionales y para usuarios avanzados. <br>
                        <strong>CSS Classes:</strong> Agregar clases CSS separadas por espacios (ej: btn-primary highlight)<br>
                        <strong>Attributes:</strong> JSON con atributos HTML personalizados
                    </p>
                </div>
            ''')
        }),
        
        ('📅 INFORMACIÓN DEL SISTEMA', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'duplicate_menu', 
        'activate_menus', 
        'deactivate_menus', 
        'convert_to_megamenu',
        'move_to_header',
        'move_to_footer'
    ]
    
    # Métodos readonly personalizados
    
    def quick_guide(self, obj):
        """Campo vacío solo para mostrar la guía"""
        return ""
    quick_guide.short_description = ""
    
    def hierarchy_info(self, obj):
        """Muestra información de jerarquía"""
        if obj.pk:
            ancestors = obj.get_ancestors()
            descendants = obj.get_descendants()
            siblings = obj.get_siblings()
            
            # Construir ruta
            path_items = [a.name for a in ancestors] + [obj.name]
            path = ' → '.join(path_items)
            
            return format_html(
                '''
                <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;">
                    <h3 style="margin: 0 0 15px 0; color: #065f46; font-size: 16px;">📊 Información de Jerarquía</h3>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #065f46; font-weight: 600;">📍 Ubicación:</td>
                            <td style="padding: 8px 0;">
                                <code style="background: white; padding: 6px 12px; border-radius: 6px; display: inline-block; color: #047857;">{}</code>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #065f46; font-weight: 600;">📈 Nivel:</td>
                            <td style="padding: 8px 0;">
                                <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">Nivel {}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #065f46; font-weight: 600;">👪 Ancestros:</td>
                            <td style="padding: 8px 0; color: #047857;">{}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #065f46; font-weight: 600;">👶 Descendientes:</td>
                            <td style="padding: 8px 0; color: #047857;">{}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #065f46; font-weight: 600;">👥 Hermanos:</td>
                            <td style="padding: 8px 0; color: #047857;">{}</td>
                        </tr>
                    </table>
                </div>
                ''',
                path,
                obj.level,
                len(ancestors),
                len(descendants),
                len(siblings)
            )
        return "Guarda primero para ver la información de jerarquía"
    hierarchy_info.short_description = "Jerarquía"
    
    def preview_url_box(self, obj):
        """Preview de la URL final con copy button"""
        if obj.pk:
            url = obj.get_url()
            return format_html(
                '''
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin: 10px 0;">
                    <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">🔗 URL Final del Menú</h3>
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
                        <code style="color: white; font-size: 15px; font-weight: 600; flex: 1;">{}</code>
                        <button type="button" 
                                onclick="navigator.clipboard.writeText('{}'); alert('✅ URL copiada al portapapeles!');" 
                                style="background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-left: 15px;">
                            📋 Copiar
                        </button>
                    </div>
                    <div style="margin-top: 12px; font-size: 13px; color: rgba(255,255,255,0.9);">
                        💡 Esta es la URL que se usará cuando el usuario haga clic en este menú
                    </div>
                </div>
                ''',
                url,
                url
            )
        return "Guarda primero para ver la URL final"
    preview_url_box.short_description = "Preview URL"
    
    def image_preview_large(self, obj):
        """Preview de imagen grande"""
        if obj.image:
            return format_html(
                '''
                <div style="margin: 15px 0;">
                    <img src="{}" style="max-width: 500px; max-height: 400px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);" />
                    <div style="margin-top: 12px;">
                        <a href="{}" target="_blank" style="background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; display: inline-block;">
                            🔗 Ver imagen completa
                        </a>
                    </div>
                </div>
                ''',
                obj.image.url,
                obj.image.url
            )
        return format_html(
            '<p style="color: #9ca3af; padding: 30px; background: #f9fafb; border-radius: 8px; text-align: center; border: 2px dashed #d1d5db;">📷 No hay imagen subida</p>'
        )
    image_preview_large.short_description = 'Vista Previa de Imagen'
    
    # Métodos de list_display
    
    def indented_title(self, obj):
        """Título con indentación y icono"""
        indent = '—' * obj.level
        icon_html = ''
        if obj.icon:
            icon_html = f'<i class="{obj.icon}" style="margin-right: 8px; color: #3b82f6; font-size: 16px;"></i>'
        
        featured_badge = ''
        if obj.is_featured:
            featured_badge = '<span style="background: #fbbf24; color: white; padding: 2px 6px; border-radius: 8px; font-size: 9px; margin-left: 8px; font-weight: 600;">★ DESTACADO</span>'
        
        return format_html(
            '<span style="margin-left: {}px; display: inline-flex; align-items: center;">{} {}{}{}</span>',
            obj.level * 30,
            indent,
            icon_html,
            obj.name,
            featured_badge
        )
    indented_title.short_description = 'Menú'
    
    def menu_type_badge(self, obj):
        """Badge de tipo de menú"""
        colors = {
            'header': '#3b82f6',
            'footer': '#6b7280',
            'mobile': '#8b5cf6',
            'sidebar': '#10b981',
            'custom': '#f59e0b',
        }
        color = colors.get(obj.menu_type, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">{}</span>',
            color,
            obj.get_menu_type_display()
        )
    menu_type_badge.short_description = 'Tipo'
    menu_type_badge.admin_order_field = 'menu_type'
    
    def link_type_badge(self, obj):
        """Badge de tipo de enlace"""
        colors = {
            'url': '#0ea5e9',
            'category': '#8b5cf6',
            'page': '#10b981',
            'external': '#f59e0b',
            'megamenu': '#ec4899',
        }
        icons = {
            'url': '🔗',
            'category': '🏷️',
            'page': '📄',
            'external': '🌐',
            'megamenu': '📑',
        }
        color = colors.get(obj.link_type, '#6b7280')
        icon = icons.get(obj.link_type, '🔗')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">{} {}</span>',
            color,
            icon,
            obj.get_link_type_display()
        )
    link_type_badge.short_description = 'Enlace'
    link_type_badge.admin_order_field = 'link_type'
    
    def url_display(self, obj):
        """Muestra la URL final"""
        url = obj.get_url()
        display_url = url if len(url) <= 35 else url[:32] + '...'
        
        return format_html(
            '<code style="background: #f3f4f6; padding: 6px 10px; border-radius: 6px; font-size: 11px; color: #1f2937; cursor: pointer; display: inline-block;" '
            'title="{}" onclick="navigator.clipboard.writeText(\'{}\'); alert(\'✅ URL copiada!\');">{}</code>',
            url,
            url,
            display_url
        )
    url_display.short_description = 'URL'
    
    def icon_display(self, obj):
        """Muestra el icono"""
        if obj.icon:
            return format_html(
                '<div style="text-align: center;">'
                '<i class="{}" style="font-size: 20px; color: #3b82f6;"></i>'
                '<div style="font-size: 9px; color: #9ca3af; margin-top: 2px;">{}</div>'
                '</div>',
                obj.icon,
                obj.icon
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Sin icono</span>')
    icon_display.short_description = 'Icono'
    
    def status_badge(self, obj):
        """Badge de estado"""
        if obj.is_active:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600;">● ACTIVO</span>'
            )
        return format_html(
            '<span style="background: #6b7280; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600;">○ INACTIVO</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'
    
    # Acciones
    
    @admin.action(description='🔄 Duplicar menús seleccionados')
    def duplicate_menu(self, request, queryset):
        count = 0
        for menu in queryset:
            menu.pk = None
            menu.name = f"{menu.name} (Copia)"
            menu.slug = ''
            menu.is_active = False
            menu.save()
            count += 1
        self.message_user(request, f"✅ {count} menú(s) duplicado(s)")
    
    @admin.action(description='✅ Activar menús')
    def activate_menus(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"✅ {count} menú(s) activado(s)")
    
    @admin.action(description='⏸️ Desactivar menús')
    def deactivate_menus(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"⏸️ {count} menú(s) desactivado(s)")
    
    @admin.action(description='🎯 Convertir a Mega Menú')
    def convert_to_megamenu(self, request, queryset):
        count = queryset.update(link_type='megamenu', mega_menu_columns=3)
        self.message_user(request, f"🎯 {count} menú(s) convertido(s) a mega menú")
    
    @admin.action(description='📍 Mover a Header')
    def move_to_header(self, request, queryset):
        count = queryset.update(menu_type='header')
        self.message_user(request, f"📍 {count} menú(s) movido(s) a Header")
    
    @admin.action(description='📍 Mover a Footer')
    def move_to_footer(self, request, queryset):
        count = queryset.update(menu_type='footer')
        self.message_user(request, f"📍 {count} menú(s) movido(s) a Footer")


# ============================================================================
# PAGE ADMIN (ULTRA MEJORADO)
# ============================================================================

class PageAdminForm(forms.ModelForm):
    """Form con validaciones avanzadas"""
    
    class Meta:
        model = Page
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Ej: Política de Privacidad, Términos y Condiciones',
                'style': 'width: 100%; font-size: 14px;',
                'class': 'vTextField'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'politica-de-privacidad (se genera automáticamente)',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Resumen corto de la página (máx 500 caracteres)',
                'style': 'width: 100%;',
                'maxlength': 500
            }),
            'meta_title': forms.TextInput(attrs={
                'placeholder': 'Título para SEO (máx 70 caracteres)',
                'style': 'width: 100%;',
                'maxlength': 70,
                'class': 'vTextField'
            }),
            'meta_description': forms.TextInput(attrs={
                'placeholder': 'Descripción para SEO (máx 160 caracteres)',
                'style': 'width: 100%;',
                'maxlength': 160,
                'class': 'vTextField'
            }),
            'meta_keywords': forms.TextInput(attrs={
                'placeholder': 'privacidad, datos, protección, legal',
                'style': 'width: 100%;',
                'class': 'vTextField'
            }),
            'order': forms.NumberInput(attrs={
                'min': 0,
                'style': 'width: 100px;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Slug auto-generado
        if 'slug' in self.fields:
            if not self.instance.pk:
                self.fields['slug'].required = False
                self.fields['slug'].help_text = "💡 Dejar vacío para generar del título"
        
        # Help texts mejorados
        if 'page_type' in self.fields:
            self.fields['page_type'].help_text = "📂 Tipo de página para organización"
        
        if 'template' in self.fields:
            self.fields['template'].help_text = "🎨 Plantilla de diseño a usar"
        
        if 'show_in_menu' in self.fields:
            self.fields['show_in_menu'].help_text = "📍 Sugerir esta página en menús automáticos"
        
        if 'require_auth' in self.fields:
            self.fields['require_auth'].help_text = "🔒 Requiere que el usuario esté logueado"
    
    def clean_meta_title(self):
        """Validar longitud de meta_title"""
        meta_title = self.cleaned_data.get('meta_title', '')
        if meta_title and len(meta_title) > 70:
            raise ValidationError('⚠️ El meta título no debe superar los 70 caracteres')
        return meta_title
    
    def clean_meta_description(self):
        """Validar longitud de meta_description"""
        meta_description = self.cleaned_data.get('meta_description', '')
        if meta_description and len(meta_description) > 160:
            raise ValidationError('⚠️ La meta descripción no debe superar los 160 caracteres')
        return meta_description


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin ultra mejorado para páginas"""
    
    form = PageAdminForm
    
    list_display = [
        'id_badge',
        'title',
        'slug_display',
        'page_type_badge',
        'template_badge',
        'status_badge',
        'reading_time_badge',
        'published_at',
        'updated_at',
    ]
    
    list_display_links = ['title']
    list_filter = ['page_type', 'template', 'is_published', 'show_in_menu', 'require_auth']
    search_fields = ['title', 'slug', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'reading_time_display',
        'featured_image_preview',
        'seo_preview',
        'quick_guide_page'
    ]
    
    fieldsets = (
        ('🎯 GUÍA RÁPIDA', {
            'fields': ('quick_guide_page',),
            'description': mark_safe('''
                <div style="background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0;">
                    <h2 style="margin: 0 0 20px 0; color: white; font-size: 22px;">📄 Guía Rápida: Crear una Página</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                            <div style="font-size: 36px; margin-bottom: 12px;">1️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white;">Contenido Principal</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li>Escribe el <strong>Título</strong></li>
                                <li>Usa el <strong>Editor</strong> para el contenido</li>
                                <li>Agrega un <strong>Extracto</strong> corto</li>
                            </ul>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                            <div style="font-size: 36px; margin-bottom: 12px;">2️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white;">Tipo y Plantilla</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Legal:</strong> Privacidad, Términos</li>
                                <li><strong>About:</strong> Sobre Nosotros</li>
                                <li><strong>Help:</strong> FAQ, Ayuda</li>
                            </ul>
                        </div>
                        
                        <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px;">
                            <div style="font-size: 36px; margin-bottom: 12px;">3️⃣</div>
                            <h3 style="margin: 0 0 12px 0; color: white;">SEO (Opcional)</h3>
                            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                <li><strong>Meta Título:</strong> Máx 70 chars</li>
                                <li><strong>Meta Descripción:</strong> Máx 160 chars</li>
                                <li><strong>Keywords:</strong> 5-10 palabras</li>
                            </ul>
                        </div>
                        
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <strong>✅ Checklist antes de publicar:</strong>
                        <ul style="margin: 8px 0; padding-left: 20px; columns: 2;">
                            <li>Título claro y descriptivo</li>
                            <li>Contenido completo y formateado</li>
                            <li>Extracto agregado</li>
                            <li>Imagen destacada (opcional)</li>
                            <li>Meta título y descripción</li>
                            <li>Tipo de página correcto</li>
                        </ul>
                    </div>
                </div>
            ''')
        }),
        
        ('📝 CONTENIDO PRINCIPAL', {
            'fields': ('title', 'slug', 'content', 'excerpt'),
        }),
        
        ('📂 TIPO Y PLANTILLA', {
            'fields': ('page_type', 'template'),
            'description': mark_safe('''
                <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <strong style="color: #0369a1;">💡 Tipos de Página:</strong>
                    <ul style="margin: 8px 0;">
                        <li><strong>Legal:</strong> Privacidad, Términos, Cookies</li>
                        <li><strong>Institucional:</strong> Sobre Nosotros, Equipo, Historia</li>
                        <li><strong>Ayuda:</strong> FAQ, Guías, Tutoriales</li>
                        <li><strong>Políticas:</strong> Devoluciones, Envíos, Garantía</li>
                        <li><strong>Personalizada:</strong> Cualquier otro tipo</li>
                    </ul>
                </div>
            ''')
        }),
        
        ('🖼️ IMAGEN DESTACADA', {
            'fields': ('featured_image', 'featured_image_preview'),
            'classes': ('collapse',),
        }),
        
        ('🔍 SEO (Optimización para Buscadores)', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'seo_preview'),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 15px 0; border-radius: 8px;">
                    <h3 style="margin: 0 0 15px 0; color: #92400e;">🎯 Tips de SEO</h3>
                    
                    <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 12px;">
                        <strong style="color: #92400e;">Meta Título (70 caracteres máx):</strong>
                        <ul style="margin: 8px 0;">
                            <li>Incluye palabra clave principal</li>
                            <li>Hazlo atractivo para clicks</li>
                            <li>Ejemplo: "Política de Privacidad | Tu Tienda 2024"</li>
                        </ul>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 12px;">
                        <strong style="color: #92400e;">Meta Descripción (160 caracteres máx):</strong>
                        <ul style="margin: 8px 0;">
                            <li>Resume el contenido</li>
                            <li>Incluye llamada a la acción</li>
                            <li>Usa palabras clave naturalmente</li>
                        </ul>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 6px;">
                        <strong style="color: #92400e;">Keywords (5-10 palabras):</strong>
                        <ul style="margin: 8px 0;">
                            <li>Separa con comas</li>
                            <li>Usa variaciones de palabras clave</li>
                            <li>Ejemplo: "privacidad, datos personales, protección datos, gdpr"</li>
                        </ul>
                    </div>
                </div>
            ''')
        }),
        
        ('⚙️ CONFIGURACIÓN', {
            'fields': (
                'is_published',
                'published_at',
                'show_in_menu',
                'require_auth',
                'order'
            ),
        }),
        
        ('📅 INFORMACIÓN DEL SISTEMA', {
            'fields': ('reading_time_display', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'publish_pages',
        'unpublish_pages',
        'duplicate_page',
        'mark_show_in_menu',
        'mark_hide_in_menu'
    ]
    
    # Métodos readonly
    
    def quick_guide_page(self, obj):
        return ""
    quick_guide_page.short_description = ""
    
    def reading_time_display(self, obj):
        """Muestra el tiempo de lectura estimado"""
        reading_time = obj.get_reading_time() if obj.pk else 0
        
        return format_html(
            '''
            <div style="background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <div style="color: white; font-size: 14px; margin-bottom: 8px; font-weight: 600;">📖 TIEMPO DE LECTURA ESTIMADO</div>
                <div style="color: white; font-size: 48px; font-weight: 700; margin: 10px 0;">{} min</div>
                <div style="color: rgba(255,255,255,0.9); font-size: 13px;">
                    (Basado en ~200 palabras por minuto)
                </div>
            </div>
            ''',
            reading_time
        )
    reading_time_display.short_description = 'Tiempo de Lectura'
    
    def featured_image_preview(self, obj):
        """Preview de imagen destacada"""
        if obj.featured_image:
            return format_html(
                '''
                <div style="margin: 15px 0;">
                    <img src="{}" style="max-width: 600px; max-height: 400px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); display: block; margin-bottom: 15px;" />
                    <div style="display: flex; gap: 10px;">
                        <a href="{}" target="_blank" style="background: #3b82f6; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px;">
                            🔗 Ver imagen completa
                        </a>
                        <button type="button" onclick="navigator.clipboard.writeText('{}'); alert('✅ URL copiada!');" style="background: #10b981; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; display: inline-flex; align-items: center; gap: 8px;">
                            📋 Copiar URL
                        </button>
                    </div>
                </div>
                ''',
                obj.featured_image.url,
                obj.featured_image.url,
                obj.featured_image.url
            )
        return format_html(
            '<div style="padding: 40px; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius: 10px; text-align: center; border: 2px dashed #9ca3af;">'
            '<div style="font-size: 48px; margin-bottom: 12px;">📷</div>'
            '<div style="color: #6b7280; font-size: 16px; font-weight: 600;">No hay imagen destacada</div>'
            '<div style="color: #9ca3af; font-size: 13px; margin-top: 8px;">Sube una imagen para mejorar el SEO</div>'
            '</div>'
        )
    featured_image_preview.short_description = 'Vista Previa de Imagen'
    
    def seo_preview(self, obj):
        """Preview de cómo se verá en Google"""
        meta_title = obj.meta_title or obj.title or "Título de la página"
        meta_desc = obj.meta_description or obj.excerpt or "Descripción de la página"
        slug = obj.slug or "pagina"
        
        # Contar caracteres
        title_count = len(meta_title)
        desc_count = len(meta_desc)
        
        title_color = '#10b981' if title_count <= 70 else '#ef4444'
        desc_color = '#10b981' if desc_count <= 160 else '#ef4444'
        
        return format_html(
            '''
            <div style="background: #f9fafb; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <h3 style="margin: 0 0 20px 0; color: #111827; font-size: 18px; display: flex; align-items: center; gap: 10px;">
                    🔍 Preview en Resultados de Google
                </h3>
                
                <div style="background: white; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; max-width: 600px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="color: #1a0dab; font-size: 20px; font-weight: 400; margin-bottom: 4px; line-height: 1.3;">
                        {}
                    </div>
                    <div style="color: #006621; font-size: 14px; margin-bottom: 6px;">
                        tu-sitio.com/page/{}
                    </div>
                    <div style="color: #545454; font-size: 14px; line-height: 1.58;">
                        {}
                    </div>
                </div>
                
                <div style="margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid {};">
                        <strong style="color: #374151; font-size: 13px;">Meta Título:</strong>
                        <div style="margin-top: 8px;">
                            <span style="color: {}; font-weight: 700; font-size: 20px;">{}</span>
                            <span style="color: #9ca3af; font-size: 13px;"> / 70</span>
                        </div>
                        <div style="margin-top: 4px; font-size: 11px; color: #6b7280;">
                            {} caracteres restantes
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid {};">
                        <strong style="color: #374151; font-size: 13px;">Meta Descripción:</strong>
                        <div style="margin-top: 8px;">
                            <span style="color: {}; font-weight: 700; font-size: 20px;">{}</span>
                            <span style="color: #9ca3af; font-size: 13px;"> / 160</span>
                        </div>
                        <div style="margin-top: 4px; font-size: 11px; color: #6b7280;">
                            {} caracteres restantes
                        </div>
                    </div>
                </div>
                
                <div style="background: #dbeafe; padding: 12px; border-radius: 6px; margin-top: 15px; border-left: 4px solid #3b82f6;">
                    <strong style="color: #1e40af; font-size: 13px;">💡 Tip:</strong>
                    <span style="color: #1e3a8a; font-size: 13px;">
                        Los títulos y descripciones óptimos mejoran el CTR (Click-Through Rate) en un 20-30%
                    </span>
                </div>
            </div>
            ''',
            meta_title,
            slug,
            meta_desc[:160],
            title_color,
            title_color,
            title_count,
            70 - title_count,
            desc_color,
            desc_color,
            desc_count,
            160 - desc_count
        )
    seo_preview.short_description = 'Preview SEO en Google'
    
    # Métodos de list_display
    
    def id_badge(self, obj):
        return format_html(
            '<span style="background: #3b82f6; color: white; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-family: monospace;">#{}</span>',
            obj.id
        )
    id_badge.short_description = 'ID'
    id_badge.admin_order_field = 'id'
    
    def slug_display(self, obj):
        return format_html(
            '<code style="background: #f3f4f6; padding: 6px 10px; border-radius: 6px; font-size: 11px; color: #1f2937; cursor: pointer;" '
            'title="Click para copiar" onclick="navigator.clipboard.writeText(\'{}\'); alert(\'✅ Slug copiado!\');">{}</code>',
            obj.slug,
            obj.slug[:25] + '...' if len(obj.slug) > 25 else obj.slug
        )
    slug_display.short_description = 'Slug'
    slug_display.admin_order_field = 'slug'
    
    def page_type_badge(self, obj):
        colors = {
            'legal': '#ef4444',
            'about': '#3b82f6',
            'help': '#10b981',
            'policy': '#f59e0b',
            'custom': '#6b7280',
        }
        icons = {
            'legal': '⚖️',
            'about': '🏢',
            'help': '❓',
            'policy': '📋',
            'custom': '📄',
        }
        color = colors.get(obj.page_type, '#6b7280')
        icon = icons.get(obj.page_type, '📄')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; white-space: nowrap;">{} {}</span>',
            color,
            icon,
            obj.get_page_type_display()
        )
    page_type_badge.short_description = 'Tipo'
    page_type_badge.admin_order_field = 'page_type'
    
    def template_badge(self, obj):
        return format_html(
            '<span style="background: #8b5cf6; color: white; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600;">{}</span>',
            obj.get_template_display()
        )
    template_badge.short_description = 'Plantilla'
    template_badge.admin_order_field = 'template'
    
    def status_badge(self, obj):
        if obj.is_currently_published():
            return format_html(
                '<span style="background: #10b981; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">'
                '<span style="display: inline-block; width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite;"></span>'
                'PUBLICADO'
                '</span>'
            )
        elif obj.is_published and obj.published_at:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600;">⏰ PROGRAMADO</span>'
            )
        return format_html(
            '<span style="background: #6b7280; color: white; padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 600;">○ BORRADOR</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_published'
    
    def reading_time_badge(self, obj):
        time = obj.get_reading_time()
        return format_html(
            '<div style="text-align: center;">'
            '<div style="background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block;">📖 {} min</div>'
            '</div>',
            time
        )
    reading_time_badge.short_description = 'Lectura'
    
    # Acciones
    
    @admin.action(description='✅ Publicar páginas seleccionadas')
    def publish_pages(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f"✅ {count} página(s) publicada(s)")
    
    @admin.action(description='📝 Convertir a borrador')
    def unpublish_pages(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f"📝 {count} página(s) convertida(s) a borrador")
    
    @admin.action(description='🔄 Duplicar páginas')
    def duplicate_page(self, request, queryset):
        count = 0
        for page in queryset:
            page.pk = None
            page.title = f"{page.title} (Copia)"
            page.slug = ''
            page.is_published = False
            page.published_at = None
            page.save()
            count += 1
        self.message_user(request, f"🔄 {count} página(s) duplicada(s)")
    
    @admin.action(description='📍 Marcar "Mostrar en menú"')
    def mark_show_in_menu(self, request, queryset):
        count = queryset.update(show_in_menu=True)
        self.message_user(request, f"📍 {count} página(s) marcada(s) para mostrar en menú")
    
    @admin.action(description='🚫 Ocultar de menú')
    def mark_hide_in_menu(self, request, queryset):
        count = queryset.update(show_in_menu=False)
        self.message_user(request, f"🚫 {count} página(s) ocultada(s) del menú")
    
    class Media:
        css = {
            'all': ('admin/css/page_admin.css',)
        }
        js = ('admin/js/page_admin.js',)