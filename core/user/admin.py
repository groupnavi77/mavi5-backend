# core/user/admin.py - ADMINISTRACIÓN COMPLETA

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    UserAccount, 
    UserProfile, 
    TokenBlacklist,
    Role,
    Permission,
    TwoFactorAuth,
    Webhook,
    WebhookLog,
    AuthLog
)


# ==============================================================================
# INLINE ADMINS
# ==============================================================================

class UserProfileInline(admin.StackedInline):
    """Inline para el perfil del usuario."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'
    fields = ('phone', 'bio')


class AuthLogInline(admin.TabularInline):
    """Inline para ver logs recientes del usuario."""
    model = AuthLog
    extra = 0
    max_num = 10
    can_delete = False
    readonly_fields = ('event_type', 'ip_address', 'success', 'timestamp', 'details')
    fields = readonly_fields
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request, obj=None):
        return False


# ==============================================================================
# USER ACCOUNT ADMIN
# ==============================================================================

@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """Administración personalizada de usuarios."""
    
    # Inline
    inlines = [UserProfileInline, AuthLogInline]
    
    # Campos que se muestran en la lista
    list_display = [
        'email', 
        'full_name', 
        'is_verified_badge',
        'provider_badge',
        'is_active', 
        'is_staff',
        'has_2fa_badge',
        'roles_display',
        'last_login_display',
        'created_at'
    ]
    
    # Filtros laterales
    list_filter = [
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'is_verified',
        'provider',
        'created_at',
        'last_login'
    ]
    
    # Búsqueda
    search_fields = ['email', 'first_name', 'last_name']
    
    # Orden por defecto
    ordering = ['-created_at']
    
    # Campos de solo lectura
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'last_password_reset',
        'last_login',
        'activity_summary'
    ]
    
    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Autenticación', {
            'fields': ('password', 'provider', 'is_verified', 'last_password_reset')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Roles Personalizados', {
            'fields': ('roles',),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Actividad', {
            'fields': ('activity_summary',),
            'classes': ('collapse',)
        })
    )
    
    # Configuración para agregar usuario
    add_fieldsets = (
        ('Crear Usuario', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_verified'),
        }),
    )
    
    # Configuración de filtros
    filter_horizontal = ('groups', 'user_permissions', 'roles')
    
    # Acciones personalizadas
    actions = [
        'activate_users',
        'deactivate_users',
        'verify_users',
        'unverify_users',
        'make_staff',
        'remove_staff'
    ]
    
    # Métodos personalizados para la lista
    
    def full_name(self, obj):
        """Nombre completo del usuario."""
        return f"{obj.first_name} {obj.last_name}".strip() or "-"
    full_name.short_description = 'Nombre Completo'
    
    def is_verified_badge(self, obj):
        """Badge para verificación de email."""
        if obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">✓ Verificado</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">⚠ Sin verificar</span>'
        )
    is_verified_badge.short_description = 'Verificación'
    
    def provider_badge(self, obj):
        """Badge para el proveedor de autenticación."""
        colors = {
            'email': '#6c757d',
            'google': '#4285f4',
            'facebook': '#1877f2',
            'github': '#333333'
        }
        color = colors.get(obj.provider, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.provider.upper()
        )
    provider_badge.short_description = 'Proveedor'
    
    def has_2fa_badge(self, obj):
        """Badge para 2FA."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=obj)
            if two_factor.is_enabled:
                return format_html(
                    '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                    'border-radius: 3px; font-size: 11px;">🔐 2FA</span>'
                )
        except TwoFactorAuth.DoesNotExist:
            pass
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">✗ Sin 2FA</span>'
        )
    has_2fa_badge.short_description = '2FA'
    
    def roles_display(self, obj):
        """Muestra los roles del usuario."""
        if hasattr(obj, 'roles'):
            roles = obj.roles.all()[:3]
            if roles:
                role_names = ', '.join([role.name for role in roles])
                count = obj.roles.count()
                if count > 3:
                    role_names += f' (+{count - 3})'
                return role_names
        return '-'
    roles_display.short_description = 'Roles'
    
    def last_login_display(self, obj):
        """Muestra el último login de forma amigable."""
        if obj.last_login:
            delta = timezone.now() - obj.last_login
            if delta < timedelta(minutes=5):
                return format_html('<span style="color: #28a745;">Ahora</span>')
            elif delta < timedelta(hours=1):
                return format_html('<span style="color: #28a745;">Hace {} min</span>', int(delta.seconds / 60))
            elif delta < timedelta(days=1):
                return format_html('<span style="color: #ffc107;">Hace {} hr</span>', int(delta.seconds / 3600))
            elif delta < timedelta(days=7):
                return format_html('<span>Hace {} días</span>', delta.days)
            else:
                return obj.last_login.strftime('%d/%m/%Y')
        return '-'
    last_login_display.short_description = 'Último Login'
    
    def activity_summary(self, obj):
        """Resumen de actividad del usuario."""
        total_logins = AuthLog.objects.filter(
            user=obj, 
            event_type='login',
            success=True
        ).count()
        
        failed_logins = AuthLog.objects.filter(
            user=obj,
            event_type='login_failed'
        ).count()
        
        last_7_days = timezone.now() - timedelta(days=7)
        recent_activity = AuthLog.objects.filter(
            user=obj,
            timestamp__gte=last_7_days
        ).count()
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Logins exitosos:</strong> {}<br>'
            '<strong>Intentos fallidos:</strong> {}<br>'
            '<strong>Actividad (7 días):</strong> {} eventos'
            '</div>',
            total_logins,
            failed_logins,
            recent_activity
        )
    activity_summary.short_description = 'Resumen de Actividad'
    
    # Acciones masivas
    
    @admin.action(description='✓ Activar usuarios seleccionados')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuarios activados.')
    
    @admin.action(description='✗ Desactivar usuarios seleccionados')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuarios desactivados.')
    
    @admin.action(description='✓ Verificar email de usuarios')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} usuarios verificados.')
    
    @admin.action(description='✗ Quitar verificación')
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} usuarios sin verificar.')
    
    @admin.action(description='👑 Hacer staff')
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} usuarios ahora son staff.')
    
    @admin.action(description='👤 Quitar staff')
    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'{updated} usuarios ya no son staff.')


# ==============================================================================
# TOKEN BLACKLIST ADMIN
# ==============================================================================

@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    """Administración de tokens revocados."""
    
    list_display = ['user', 'token_preview', 'expires_at', 'is_expired']
    list_filter = ['expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'user', 'expires_at']
    ordering = ['-expires_at']
    
    def token_preview(self, obj):
        """Muestra preview del token."""
        return obj.token[:20] + '...' if len(obj.token) > 20 else obj.token
    token_preview.short_description = 'Token'
    
    def is_expired(self, obj):
        """Badge de expiración."""
        if obj.expires_at < timezone.now():
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px;">Expirado</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px;">Activo</span>'
        )
    is_expired.short_description = 'Estado'
    
    def has_add_permission(self, request):
        return False


# ==============================================================================
# ROLES Y PERMISOS ADMIN
# ==============================================================================

class PermissionInline(admin.TabularInline):
    """Inline para permisos en roles."""
    model = Role.permissions.through
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Administración de roles."""
    
    list_display = ['name', 'description', 'is_system_role', 'permissions_count', 'users_count', 'created_at']
    list_filter = ['is_system_role', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Rol', {
            'fields': ('name', 'description', 'is_system_role')
        }),
        ('Permisos', {
            'fields': ('permissions',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Permisos'
    
    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = 'Usuarios'
    
    def delete_model(self, request, obj):
        """Evita eliminar roles del sistema."""
        if obj.is_system_role:
            self.message_user(request, 'No se pueden eliminar roles del sistema.', level='ERROR')
            return
        super().delete_model(request, obj)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Administración de permisos."""
    
    list_display = ['code', 'name', 'module', 'roles_count']
    list_filter = ['module']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at']
    ordering = ['module', 'code']
    
    def roles_count(self, obj):
        return obj.roles.count()
    roles_count.short_description = 'En Roles'


# ==============================================================================
# 2FA ADMIN
# ==============================================================================

@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """Administración de 2FA."""
    
    list_display = ['user', 'is_enabled_badge', 'last_used', 'backup_codes_count', 'created_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['secret_key', 'created_at', 'last_used']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'is_enabled')
        }),
        ('Configuración', {
            'fields': ('secret_key', 'backup_codes')
        }),
        ('Información', {
            'fields': ('created_at', 'last_used')
        })
    )
    
    def is_enabled_badge(self, obj):
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px;">Inactivo</span>'
        )
    is_enabled_badge.short_description = 'Estado'
    
    def backup_codes_count(self, obj):
        return len(obj.backup_codes) if obj.backup_codes else 0
    backup_codes_count.short_description = 'Códigos Backup'


# ==============================================================================
# WEBHOOKS ADMIN
# ==============================================================================

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    """Administración de webhooks."""
    
    list_display = ['name', 'url', 'is_active_badge', 'events_display', 'logs_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['secret', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('name', 'url', 'is_active')
        }),
        ('Configuración', {
            'fields': ('events', 'secret', 'headers')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px;">Inactivo</span>'
        )
    is_active_badge.short_description = 'Estado'
    
    def events_display(self, obj):
        return ', '.join(obj.events[:3]) + ('...' if len(obj.events) > 3 else '')
    events_display.short_description = 'Eventos'
    
    def logs_count(self, obj):
        return obj.logs.count()
    logs_count.short_description = 'Logs'


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Administración de logs de webhooks."""
    
    list_display = ['webhook', 'event_type', 'success_badge', 'response_status', 'attempts', 'delivered_at']
    list_filter = ['success', 'event_type', 'delivered_at']
    search_fields = ['webhook__name', 'event_type']
    readonly_fields = ['webhook', 'event_type', 'payload', 'response_status', 'response_body', 'success', 'error_message', 'attempts', 'delivered_at']
    ordering = ['-delivered_at']
    
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✓ Exitoso</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px;">✗ Fallido</span>'
        )
    success_badge.short_description = 'Estado'
    
    def has_add_permission(self, request):
        return False


# ==============================================================================
# AUTH LOGS ADMIN
# ==============================================================================

@admin.register(AuthLog)
class AuthLogAdmin(admin.ModelAdmin):
    """Administración de logs de autenticación."""
    
    list_display = ['user', 'event_type_badge', 'success_badge', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'success', 'timestamp']
    search_fields = ['user__email', 'ip_address', 'details']
    readonly_fields = ['user', 'event_type', 'ip_address', 'user_agent', 'success', 'details', 'timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def event_type_badge(self, obj):
        colors = {
            'login': '#28a745',
            'logout': '#6c757d',
            'login_failed': '#dc3545',
            'register': '#007bff',
            'password_reset': '#ffc107',
            'password_change': '#17a2b8',
            'email_verify': '#28a745',
            '2fa_verify': '#6f42c1',
            '2fa_failed': '#dc3545'
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.event_type.replace('_', ' ').title()
        )
    event_type_badge.short_description = 'Evento'
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')
    success_badge.short_description = '✓'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==============================================================================
# USER PROFILE ADMIN (SI NO USA INLINE)
# ==============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de usuario."""
    
    list_display = ['user', 'phone', 'bio_preview']
    search_fields = ['user__email', 'phone']
    readonly_fields = ['user']
    
    def bio_preview(self, obj):
        return obj.bio[:50] + '...' if obj.bio and len(obj.bio) > 50 else obj.bio or '-'
    bio_preview.short_description = 'Bio'