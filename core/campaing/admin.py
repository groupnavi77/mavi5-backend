from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import DiscountCampaign, CategoryDiscount

@admin.register(DiscountCampaign)
class DiscountCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'campaign_type',
        'discount_badge',
        'status_badge',
        'date_range',
        'priority',
        'is_active'
    ]
    list_filter = [
        'campaign_type',
        'discount_type',
        'is_active',
        'start_date',
        'expiration_date'
    ]
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'code': ('name',)}
    filter_horizontal = ['categories', 'products']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'code', 'description', 'campaign_type')
        }),
        ('Descuento', {
            'fields': ('discount', 'discount_type')
        }),
        ('Fechas', {
            'fields': ('start_date', 'expiration_date')
        }),
        ('Alcance', {
            'fields': ('categories', 'products'),
            'description': 'Define qué productos están incluidos en la campaña'
        }),
        ('Configuración', {
            'fields': ('is_active', 'priority'),
            'description': 'Mayor prioridad = se aplica primero'
        }),
    )
    
    def discount_badge(self, obj):
        """Muestra el descuento con badge de color"""
        if obj.discount_type == 'Percentaje':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '{}%</span>',
                obj.discount
            )
        else:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '${}</span>',
                obj.discount
            )
    discount_badge.short_description = 'Descuento'
    
    def status_badge(self, obj):
        """Muestra el estado actual de la campaña"""
        now = timezone.now()
        
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Inactiva</span>'
            )
        
        if obj.start_date > now:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">Próximamente</span>'
            )
        
        if obj.expiration_date < now:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Expirada</span>'
            )
        
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">🔥 Activa</span>'
        )
    status_badge.short_description = 'Estado'
    
    def date_range(self, obj):
        """Muestra el rango de fechas de forma compacta"""
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.expiration_date.strftime('%d/%m/%Y')}"
    date_range.short_description = 'Vigencia'
    
    actions = ['activate_campaigns', 'deactivate_campaigns']
    
    def activate_campaigns(self, request, queryset):
        """Acción para activar campañas seleccionadas"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} campaña(s) activada(s).')
    activate_campaigns.short_description = 'Activar campañas seleccionadas'
    
    def deactivate_campaigns(self, request, queryset):
        """Acción para desactivar campañas seleccionadas"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} campaña(s) desactivada(s).')
    deactivate_campaigns.short_description = 'Desactivar campañas seleccionadas'


@admin.register(CategoryDiscount)
class CategoryDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'discount_badge',
        'status_badge',
        'is_active'
    ]
    list_filter = ['category', 'discount_type', 'is_active']
    search_fields = ['name', 'category__name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'category')
        }),
        ('Descuento', {
            'fields': ('discount', 'discount_type')
        }),
        ('Fechas (Opcional)', {
            'fields': ('start_date', 'expiration_date'),
            'description': 'Dejar vacío para descuento permanente'
        }),
        ('Configuración', {
            'fields': ('is_active',)
        }),
    )
    
    def discount_badge(self, obj):
        """Muestra el descuento con badge"""
        if obj.discount_type == 'Percentaje':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '{}%</span>',
                obj.discount
            )
        else:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '${}</span>',
                obj.discount
            )
    discount_badge.short_description = 'Descuento'
    
    def status_badge(self, obj):
        """Muestra si el descuento está activo"""
        if obj.is_currently_active():
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Inactivo</span>'
        )
    status_badge.short_description = 'Estado'