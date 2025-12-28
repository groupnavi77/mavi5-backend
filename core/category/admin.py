# core/category/admin.py

from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Category


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """
    Admin mejorado para categorías con soporte MPTT.
    Permite reorganizar categorías arrastrando y soltando.
    """
    
    # Configuración de MPTT draggable
    mptt_level_indent = 20
    
    # Campos en la lista
    list_display = [
        'tree_actions',
        'indented_title',
        'title',
        'slug',
        'icon_display',
        'level',
        'parent',
        'children_count',
        'image_preview',
    ]
    
    list_display_links = ['indented_title', 'title']
    
    # Filtros
    list_filter = ['level', 'parent']
    
    # Búsqueda
    search_fields = ['title', 'slug', 'description']
    
    # Campos de solo lectura
    readonly_fields = ['level', 'image_preview_large']
    
    # Campos en el formulario
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'parent')
        }),
        ('Contenido', {
            'fields': ('description', 'icon')
        }),
        ('Imagen', {
            'fields': ('cat_image', 'image_preview_large')
        }),
        ('Información del Árbol', {
            'fields': ('level',),
            'classes': ('collapse',)
        }),
    )
    
    # Prepoblar slug desde title
    prepopulated_fields = {'slug': ('title',)}
    
    # Acciones
    actions = ['make_root', 'export_to_csv']
    
    # Métodos personalizados
    
    def indented_title(self, obj):
        """
        Muestra el título con indentación visual según el nivel.
        """
        indent = '—' * obj.level
        return format_html(
            '<span style="margin-left: {}px;">{} {}</span>',
            obj.level * 20,
            indent,
            obj.title
        )
    indented_title.short_description = 'Categoría'
    
    def icon_display(self, obj):
        """Muestra el icono si existe."""
        if obj.icon:
            return format_html(
                '<i class="{}" style="font-size: 18px; color: #007bff;"></i>',
                obj.icon
            )
        return '-'
    icon_display.short_description = 'Icono'
    
    def children_count(self, obj):
        """Cuenta de hijos directos."""
        count = obj.get_children().count()
        if count > 0:
            return format_html(
                '<strong style="color: #28a745;">{}</strong> hijo(s)',
                count
            )
        return format_html('<span style="color: #999;">Sin hijos</span>')
    children_count.short_description = 'Hijos'
    
    def image_preview(self, obj):
        """Preview pequeño de la imagen en la lista."""
        if obj.cat_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.cat_image.url
            )
        return format_html('<span style="color: #999;">Sin imagen</span>')
    image_preview.short_description = 'Imagen'
    
    def image_preview_large(self, obj):
        """Preview grande de la imagen en el detalle."""
        if obj.cat_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 10px;" />',
                obj.cat_image.url
            )
        return 'No hay imagen'
    image_preview_large.short_description = 'Vista Previa'
    
    # Acciones personalizadas
    
    @admin.action(description='Convertir en categoría raíz')
    def make_root(self, request, queryset):
        """Convierte las categorías seleccionadas en raíz (sin padre)."""
        updated = 0
        for category in queryset:
            category.parent = None
            category.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} categoría(s) convertida(s) en raíz.'
        )
    
    @admin.action(description='Exportar a CSV')
    def export_to_csv(self, request, queryset):
        """Exporta las categorías seleccionadas a CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="categorias.csv"'
        response.write('\ufeff')  # BOM para Excel
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Título', 'Slug', 'Nivel', 'Padre', 'Descripción'])
        
        for category in queryset:
            writer.writerow([
                category.id,
                category.title,
                category.slug,
                category.level,
                category.parent.title if category.parent else 'Raíz',
                category.description
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} categoría(s) exportada(s).'
        )
        return response


# Versión alternativa sin drag & drop (si prefieres la vista tradicional)
"""
@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['title', 'slug', 'parent', 'level']
    list_filter = ['level', 'parent']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    
    mptt_level_indent = 20
"""