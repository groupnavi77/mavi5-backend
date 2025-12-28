# core/user/admin.py - VERSIÓN MEJORADA Y COMPLETA

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
import csv
import json

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
    extra = 0


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


class RoleMembershipInline(admin.TabularInline):
    """Inline para gestionar roles del usuario."""
    model = UserAccount.roles.through
    extra = 1
    verbose_name = 'Rol'
    verbose_name_plural = 'Roles del Usuario'


# ==============================================================================
# USER ACCOUNT ADMIN
# ==============================================================================

@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """Administración personalizada de usuarios."""
    
    # Inline
    inlines = [UserProfileInline, RoleMembershipInline, AuthLogInline]
    
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
        'created_at_display'
    ]
    
    # Filtros laterales
    list_filter = [
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'is_verified',
        'provider',
        'created_at',
        'last_login',
        'roles',
    ]
    
    # Búsqueda
    search_fields = ['email', 'first_name', 'last_name', 'id']
    
    # Orden por defecto
    ordering = ['-created_at']
    
    # Campos de solo lectura
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'last_password_reset',
        'last_login',
        'activity_summary',
        'security_info',
        'user_stats'
    ]
    
    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Autenticación', {
            'fields': ('password', 'provider', 'is_verified', 'last_password_reset'),
            'description': 'Gestión de autenticación y contraseña'
        }),
        ('Permisos de Sistema', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Roles Personalizados', {
            'fields': ('roles',),
            'description': 'Roles dinámicos con permisos personalizados'
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('user_stats', 'activity_summary', 'security_info'),
            'classes': ('collapse',)
        })
    )
    
    # Configuración para agregar usuario
    add_fieldsets = (
        ('Crear Usuario', {
            'classes': ('wide',),
            'fields': (
                'email', 
                'first_name', 
                'last_name', 
                'password1', 
                'password2', 
                'is_active', 
                'is_verified',
                'provider'
            ),
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
        'remove_staff',
        'export_users_csv',
        'export_users_json',
        'send_verification_email',
        'reset_password_and_notify',
    ]

    # URLs personalizadas
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'analytics/',
                self.admin_site.admin_view(self.analytics_view),
                name='user_analytics',
            ),
            path(
                '<int:user_id>/activity/',
                self.admin_site.admin_view(self.user_activity_view),
                name='user_activity',
            ),
            path(
                '<int:user_id>/disable-2fa/',
                self.admin_site.admin_view(self.disable_2fa_view),
                name='user_disable_2fa',
            ),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Override para agregar contexto extra a la lista."""
        extra_context = extra_context or {}
        extra_context['show_analytics_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    # Métodos personalizados para la lista
    
    def full_name(self, obj):
        """Nombre completo del usuario."""
        name = f"{obj.first_name} {obj.last_name}".strip()
        if name:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                name,
                obj.email
            )
        return obj.email
    full_name.short_description = 'Usuario'
    
    def is_verified_badge(self, obj):
        """Badge para verificación de email."""
        if obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✓ Verificado</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠ Sin verificar</span>'
        )
    is_verified_badge.short_description = 'Email'
    
    def provider_badge(self, obj):
        """Badge para el proveedor de autenticación."""
        colors = {
            'email': '#6c757d',
            'google': '#4285f4',
            'facebook': '#1877f2',
            'github': '#333333'
        }
        icons = {
            'email': '✉',
            'google': 'G',
            'facebook': 'f',
            'github': '⚡'
        }
        color = colors.get(obj.provider, '#6c757d')
        icon = icons.get(obj.provider, '?')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.provider.upper()
        )
    provider_badge.short_description = 'Método'
    
    def has_2fa_badge(self, obj):
        """Badge para 2FA."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=obj)
            if two_factor.is_enabled:
                return format_html(
                    '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                    'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                    '🔐 Activo</span>'
                )
        except TwoFactorAuth.DoesNotExist:
            pass
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">✗ Sin 2FA</span>'
        )
    has_2fa_badge.short_description = '2FA'
    
    def roles_display(self, obj):
        """Muestra los roles del usuario."""
        roles = obj.roles.all()[:3]
        if not roles:
            return format_html('<span style="color: #999;">Sin roles</span>')
        
        role_names = ', '.join([f'<strong>{role.name}</strong>' for role in roles])
        count = obj.roles.count()
        if count > 3:
            role_names += f' <span style="color: #666;">(+{count - 3})</span>'
        return format_html(role_names)
    roles_display.short_description = 'Roles'
    
    def last_login_display(self, obj):
        """Muestra el último login de forma amigable."""
        if obj.last_login:
            delta = timezone.now() - obj.last_login
            if delta < timedelta(minutes=5):
                return format_html('<span style="color: #28a745; font-weight: bold;">● Ahora</span>')
            elif delta < timedelta(hours=1):
                minutes = int(delta.seconds / 60)
                return format_html('<span style="color: #28a745;">● Hace {} min</span>', minutes)
            elif delta < timedelta(days=1):
                hours = int(delta.seconds / 3600)
                return format_html('<span style="color: #ffc107;">● Hace {} hr</span>', hours)
            elif delta < timedelta(days=7):
                return format_html('<span>Hace {} días</span>', delta.days)
            else:
                return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return format_html('<span style="color: #999;">Nunca</span>')
    last_login_display.short_description = 'Último Login'
    
    def created_at_display(self, obj):
        """Muestra la fecha de creación formateada."""
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return '-'
    created_at_display.short_description = 'Registro'
    
    def user_stats(self, obj):
        """Estadísticas del usuario."""
        try:
            two_factor = TwoFactorAuth.objects.filter(user=obj, is_enabled=True).exists()
        except:
            two_factor = False
        
        blacklisted_tokens = TokenBlacklist.objects.filter(user=obj).count()
        roles_count = obj.roles.count()
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>ID:</strong> {}<br>'
            '<strong>Roles asignados:</strong> {}<br>'
            '<strong>2FA habilitado:</strong> {}<br>'
            '<strong>Tokens revocados:</strong> {}<br>'
            '<strong>Provider:</strong> {}'
            '</div>',
            obj.id,
            roles_count,
            '✓ Sí' if two_factor else '✗ No',
            blacklisted_tokens,
            obj.provider
        )
    user_stats.short_description = 'Estadísticas del Usuario'
    
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
        
        last_ip = AuthLog.objects.filter(
            user=obj,
            event_type='login',
            success=True
        ).order_by('-timestamp').first()
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Logins exitosos:</strong> <span style="color: #28a745;">{}</span><br>'
            '<strong>Intentos fallidos:</strong> <span style="color: #dc3545;">{}</span><br>'
            '<strong>Actividad (7 días):</strong> {} eventos<br>'
            '<strong>Última IP:</strong> {}<br>'
            '<a href="{}" class="button">Ver historial completo</a>'
            '</div>',
            total_logins,
            failed_logins,
            recent_activity,
            last_ip.ip_address if last_ip else 'N/A',
            reverse('admin:user_activity', args=[obj.id])
        )
    activity_summary.short_description = 'Actividad'
    
    def security_info(self, obj):
        """Información de seguridad."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=obj)
            two_fa_status = '✓ Activo' if two_factor.is_enabled else '✗ Inactivo'
            last_2fa = two_factor.last_used.strftime('%d/%m/%Y %H:%M') if two_factor.last_used else 'Nunca'
            backup_codes = len(two_factor.backup_codes) if two_factor.backup_codes else 0
        except TwoFactorAuth.DoesNotExist:
            two_fa_status = '✗ No configurado'
            last_2fa = 'N/A'
            backup_codes = 0
        
        last_password = obj.last_password_reset.strftime('%d/%m/%Y %H:%M') if obj.last_password_reset else 'Nunca'
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>2FA:</strong> {}<br>'
            '<strong>Último uso 2FA:</strong> {}<br>'
            '<strong>Códigos backup:</strong> {}<br>'
            '<strong>Último cambio contraseña:</strong> {}<br>'
            '{}'
            '</div>',
            two_fa_status,
            last_2fa,
            backup_codes,
            last_password,
            format_html(
                '<a href="{}" class="button" style="margin-top: 10px;">Deshabilitar 2FA</a>',
                reverse('admin:user_disable_2fa', args=[obj.id])
            ) if two_fa_status == '✓ Activo' else ''
        )
    security_info.short_description = 'Seguridad'
    
    
    # Acciones masivas
    
    @admin.action(description='✓ Activar usuarios seleccionados')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} usuario(s) activado(s) exitosamente.',
            messages.SUCCESS
        )
    
    @admin.action(description='✗ Desactivar usuarios seleccionados')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} usuario(s) desactivado(s).',
            messages.WARNING
        )
    
    @admin.action(description='✓ Verificar email de usuarios')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(
            request, 
            f'{updated} usuario(s) verificado(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='✗ Quitar verificación')
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(
            request, 
            f'{updated} usuario(s) sin verificar.',
            messages.WARNING
        )
    
    @admin.action(description='👑 Hacer staff')
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(
            request, 
            f'{updated} usuario(s) ahora son staff.',
            messages.SUCCESS
        )
    
    @admin.action(description='👤 Quitar staff')
    def remove_staff(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(is_staff=False)
        if updated < queryset.count():
            self.message_user(
                request,
                'No se puede quitar staff a superusuarios.',
                messages.WARNING
            )
        self.message_user(
            request, 
            f'{updated} usuario(s) ya no son staff.',
            messages.SUCCESS
        )
    
    @admin.action(description='📥 Exportar usuarios a CSV')
    def export_users_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
        response.write('\ufeff')  # BOM para Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'Nombre', 'Apellido', 'Verificado', 
            'Activo', 'Staff', 'Provider', 'Fecha Registro', 'Último Login'
        ])
        
        for user in queryset:
            writer.writerow([
                user.id,
                user.email,
                user.first_name,
                user.last_name,
                'Sí' if user.is_verified else 'No',
                'Sí' if user.is_active else 'No',
                'Sí' if user.is_staff else 'No',
                user.provider,
                user.created_at.strftime('%Y-%m-%d %H:%M'),
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Nunca'
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} usuario(s) exportado(s) a CSV.',
            messages.SUCCESS
        )
        return response
    
    @admin.action(description='📥 Exportar usuarios a JSON')
    def export_users_json(self, request, queryset):
        users_data = []
        for user in queryset:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': user.is_verified,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'provider': user.provider,
                'roles': list(user.roles.values_list('name', flat=True)),
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            })
        
        response = HttpResponse(
            json.dumps(users_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="usuarios.json"'
        
        self.message_user(
            request,
            f'{queryset.count()} usuario(s) exportado(s) a JSON.',
            messages.SUCCESS
        )
        return response
    
    @admin.action(description='📧 Enviar email de verificación')
    def send_verification_email(self, request, queryset):
        from .api.services import UserService
        
        count = 0
        for user in queryset.filter(is_verified=False):
            try:
                UserService.send_action_email(user, 'verify')
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error enviando email a {user.email}: {str(e)}',
                    messages.ERROR
                )
        
        self.message_user(
            request,
            f'Email de verificación enviado a {count} usuario(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='🔑 Resetear contraseña y notificar')
    def reset_password_and_notify(self, request, queryset):
        from .api.services import UserService
        
        count = 0
        for user in queryset:
            try:
                UserService.send_action_email(user, 'reset')
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error enviando email a {user.email}: {str(e)}',
                    messages.ERROR
                )
        
        self.message_user(
            request,
            f'Email de reseteo enviado a {count} usuario(s).',
            messages.SUCCESS
        )
    
    # Vistas personalizadas
    
    def analytics_view(self, request):
        """Vista de analíticas de usuarios."""
        context = dict(
            self.admin_site.each_context(request),
            title='Analíticas de Usuarios',
        )
        
        # Estadísticas generales
        total_users = UserAccount.objects.count()
        verified_users = UserAccount.objects.filter(is_verified=True).count()
        active_users = UserAccount.objects.filter(is_active=True).count()
        staff_users = UserAccount.objects.filter(is_staff=True).count()
        
        # Usuarios por provider
        users_by_provider = UserAccount.objects.values('provider').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Usuarios con 2FA
        users_with_2fa = TwoFactorAuth.objects.filter(is_enabled=True).count()
        
        # Registros por mes (últimos 6 meses)
        six_months_ago = timezone.now() - timedelta(days=180)
        registrations_by_month = UserAccount.objects.filter(
            created_at__gte=six_months_ago
        ).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        # Actividad reciente
        last_7_days = timezone.now() - timedelta(days=7)
        recent_logins = AuthLog.objects.filter(
            event_type='login',
            success=True,
            timestamp__gte=last_7_days
        ).count()
        
        failed_logins = AuthLog.objects.filter(
            event_type='login_failed',
            timestamp__gte=last_7_days
        ).count()
        
        context.update({
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'users_by_provider': users_by_provider,
            'users_with_2fa': users_with_2fa,
            'registrations_by_month': registrations_by_month,
            'recent_logins': recent_logins,
            'failed_logins': failed_logins,
        })
        
        return render(request, 'admin/user/analytics.html', context)
    
    def user_activity_view(self, request, user_id):
        """Vista de actividad de un usuario específico."""
        user = UserAccount.objects.get(id=user_id)
        logs = AuthLog.objects.filter(user=user).order_by('-timestamp')[:100]
        
        context = dict(
            self.admin_site.each_context(request),
            title=f'Actividad de {user.email}',
            user=user,
            logs=logs,
        )
        
        return render(request, 'admin/user/activity.html', context)
    
    def disable_2fa_view(self, request, user_id):
        """Deshabilita 2FA de un usuario."""
        user = UserAccount.objects.get(id=user_id)
        
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            two_factor.is_enabled = False
            two_factor.save()
            
            messages.success(
                request,
                f'2FA deshabilitado para {user.email}'
            )
        except TwoFactorAuth.DoesNotExist:
            messages.warning(
                request,
                f'{user.email} no tiene 2FA configurado'
            )
        
        return redirect('admin:user_useraccount_change', user_id)


# ==============================================================================
# TOKEN BLACKLIST ADMIN
# ==============================================================================

@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    """Administración de tokens revocados."""
    
    list_display = ['user_link', 'token_preview', 'expires_at', 'is_expired', 'time_remaining']
    list_filter = ['expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'user', 'expires_at', 'created_display']
    ordering = ['-expires_at']
    date_hierarchy = 'expires_at'
    
    actions = ['delete_expired_tokens']
    
    def user_link(self, obj):
        """Link al usuario."""
        url = reverse('admin:user_useraccount_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def token_preview(self, obj):
        """Muestra preview del token."""
        token_str = str(obj.token)
        preview = token_str[:30] + '...' if len(token_str) > 30 else token_str
        return format_html(
            '<code style="background: #f5f5f5; padding: 2px 5px; border-radius: 3px;">{}</code>',
            preview
        )
    token_preview.short_description = 'Token'
    
    def is_expired(self, obj):
        """Badge de expiración."""
        if obj.expires_at < timezone.now():
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">✗ Expirado</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">✓ Activo</span>'
        )
    is_expired.short_description = 'Estado'
    
    def time_remaining(self, obj):
        """Tiempo restante."""
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: #999;">-</span>')
        
        delta = obj.expires_at - timezone.now()
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return f"{days} día(s)"
        elif hours > 0:
            return f"{hours} hora(s)"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} min"
    time_remaining.short_description = 'Tiempo Restante'
    
    def created_display(self, obj):
        """Fecha de creación formateada."""
        # Asumiendo que no tienes un campo created_at, usa expires_at - lifetime
        return format_html(
            '<div style="font-size: 12px; color: #666;">'
            'Revocado aproximadamente cuando se creó'
            '</div>'
        )
    created_display.short_description = 'Creado'
    
    @admin.action(description='🗑️ Eliminar tokens expirados')
    def delete_expired_tokens(self, request, queryset):
        """Elimina tokens que ya expiraron."""
        deleted = queryset.filter(expires_at__lt=timezone.now()).delete()
        self.message_user(
            request,
            f'{deleted[0]} token(s) expirado(s) eliminado(s).',
            messages.SUCCESS
        )
    
    def has_add_permission(self, request):
        return False


# ==============================================================================
# ROLES Y PERMISOS ADMIN
# ==============================================================================

class PermissionInline(admin.TabularInline):
    """Inline para permisos en roles."""
    model = Role.permissions.through
    extra = 1
    verbose_name = 'Permiso'
    verbose_name_plural = 'Permisos'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Administración de roles."""
    
    list_display = [
        'name', 
        'description_preview', 
        'is_system_role_badge', 
        'permissions_count', 
        'users_count', 
        'created_at_display'
    ]
    list_filter = ['is_system_role', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    readonly_fields = ['created_at', 'updated_at', 'permissions_list']
    
    fieldsets = (
        ('Información del Rol', {
            'fields': ('name', 'description', 'is_system_role')
        }),
        ('Permisos', {
            'fields': ('permissions', 'permissions_list'),
            'description': 'Permisos asignados a este rol'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['duplicate_role', 'export_role_json']
    
    def description_preview(self, obj):
        """Preview de la descripción."""
        if obj.description:
            preview = obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            return preview
        return format_html('<span style="color: #999;">Sin descripción</span>')
    description_preview.short_description = 'Descripción'
    
    def is_system_role_badge(self, obj):
        """Badge para roles del sistema."""
        if obj.is_system_role:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">🔒 Sistema</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px;">Personalizado</span>'
        )
    is_system_role_badge.short_description = 'Tipo'
    
    def permissions_count(self, obj):
        count = obj.permissions.count()
        return format_html(
            '<strong style="color: #007bff;">{}</strong> permiso(s)',
            count
        )
    permissions_count.short_description = 'Permisos'
    
    def users_count(self, obj):
        count = obj.users.count()
        if count > 0:
            url = f"{reverse('admin:user_useraccount_changelist')}?roles__id__exact={obj.id}"
            return format_html(
                '<a href="{}" style="font-weight: bold;">{} usuario(s)</a>',
                url,
                count
            )
        return format_html('<span style="color: #999;">0 usuarios</span>')
    users_count.short_description = 'Usuarios'
    
    def created_at_display(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return '-'
    created_at_display.short_description = 'Creado'
    
    def permissions_list(self, obj):
        """Lista detallada de permisos."""
        permissions = obj.permissions.all()
        if not permissions:
            return format_html('<p style="color: #999;">Sin permisos asignados</p>')
        
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for perm in permissions:
            html += f'<li><strong>{perm.code}</strong> - {perm.name}</li>'
        html += '</ul>'
        return format_html(html)
    permissions_list.short_description = 'Lista de Permisos'
    
    @admin.action(description='📋 Duplicar rol')
    def duplicate_role(self, request, queryset):
        """Duplica roles seleccionados."""
        count = 0
        for role in queryset:
            new_role = Role.objects.create(
                name=f"{role.name} (Copia)",
                description=role.description,
                is_system_role=False
            )
            new_role.permissions.set(role.permissions.all())
            count += 1
        
        self.message_user(
            request,
            f'{count} rol(es) duplicado(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='📥 Exportar a JSON')
    def export_role_json(self, request, queryset):
        """Exporta roles a JSON."""
        roles_data = []
        for role in queryset:
            roles_data.append({
                'name': role.name,
                'description': role.description,
                'permissions': list(role.permissions.values_list('code', flat=True)),
                'is_system_role': role.is_system_role,
            })
        
        response = HttpResponse(
            json.dumps(roles_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="roles.json"'
        
        self.message_user(
            request,
            f'{queryset.count()} rol(es) exportado(s).',
            messages.SUCCESS
        )
        return response
    
    def delete_model(self, request, obj):
        """Evita eliminar roles del sistema."""
        if obj.is_system_role:
            messages.error(
                request,
                'No se pueden eliminar roles del sistema.'
            )
            return
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Evita eliminar roles del sistema en masa."""
        system_roles = queryset.filter(is_system_role=True)
        if system_roles.exists():
            messages.error(
                request,
                f'No se pueden eliminar {system_roles.count()} rol(es) del sistema.'
            )
            queryset = queryset.filter(is_system_role=False)
        
        super().delete_queryset(request, queryset)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Administración de permisos."""
    
    list_display = ['code', 'name', 'module_badge', 'description_preview', 'roles_count']
    list_filter = ['module', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'roles_list']
    ordering = ['module', 'code']
    
    fieldsets = (
        ('Información del Permiso', {
            'fields': ('code', 'name', 'module', 'description')
        }),
        ('Roles que usan este permiso', {
            'fields': ('roles_list',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['export_permissions_csv']
    
    def module_badge(self, obj):
        """Badge para el módulo."""
        colors = {
            'product': '#28a745',
            'user': '#007bff',
            'order': '#ffc107',
            'review': '#17a2b8',
        }
        color = colors.get(obj.module, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.module.upper()
        )
    module_badge.short_description = 'Módulo'
    
    def description_preview(self, obj):
        """Preview de la descripción."""
        if obj.description:
            preview = obj.description[:40] + '...' if len(obj.description) > 40 else obj.description
            return preview
        return format_html('<span style="color: #999;">-</span>')
    description_preview.short_description = 'Descripción'
    
    def roles_count(self, obj):
        """Cuenta de roles."""
        count = obj.roles.count()
        if count > 0:
            return format_html(
                '<strong style="color: #007bff;">{}</strong> rol(es)',
                count
            )
        return format_html('<span style="color: #999;">0 roles</span>')
    roles_count.short_description = 'En Roles'
    
    def roles_list(self, obj):
        """Lista de roles que usan este permiso."""
        roles = obj.roles.all()
        if not roles:
            return format_html('<p style="color: #999;">No usado en ningún rol</p>')
        
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for role in roles:
            url = reverse('admin:user_role_change', args=[role.id])
            html += f'<li><a href="{url}"><strong>{role.name}</strong></a></li>'
        html += '</ul>'
        return format_html(html)
    roles_list.short_description = 'Roles'
    
    @admin.action(description='📥 Exportar a CSV')
    def export_permissions_csv(self, request, queryset):
        """Exporta permisos a CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="permisos.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['Código', 'Nombre', 'Módulo', 'Descripción', 'Roles'])
        
        for perm in queryset:
            roles = ', '.join(perm.roles.values_list('name', flat=True))
            writer.writerow([
                perm.code,
                perm.name,
                perm.module,
                perm.description,
                roles
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} permiso(s) exportado(s).',
            messages.SUCCESS
        )
        return response


# ==============================================================================
# 2FA ADMIN
# ==============================================================================

@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """Administración de 2FA."""
    
    list_display = [
        'user_link', 
        'is_enabled_badge', 
        'backup_codes_count', 
        'last_used_display', 
        'created_at_display'
    ]
    list_filter = ['is_enabled', 'created_at', 'last_used']
    search_fields = ['user__email']
    readonly_fields = ['secret_key', 'created_at', 'last_used', 'backup_codes_display']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'is_enabled')
        }),
        ('Configuración', {
            'fields': ('secret_key', 'backup_codes_display'),
            'description': 'Configuración de autenticación de dos factores'
        }),
        ('Información', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['disable_2fa', 'regenerate_backup_codes']
    
    def user_link(self, obj):
        """Link al usuario."""
        url = reverse('admin:user_useraccount_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def is_enabled_badge(self, obj):
        """Badge de estado."""
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px;">Inactivo</span>'
        )
    is_enabled_badge.short_description = 'Estado'
    
    def backup_codes_count(self, obj):
        """Cantidad de códigos backup."""
        count = len(obj.backup_codes) if obj.backup_codes else 0
        if count == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">0 códigos</span>')
        elif count < 5:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} códigos</span>', count)
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">{} códigos</span>', count)
    backup_codes_count.short_description = 'Códigos Backup'
    
    def last_used_display(self, obj):
        """Último uso."""
        if obj.last_used:
            delta = timezone.now() - obj.last_used
            if delta < timedelta(hours=1):
                return format_html('<span style="color: #28a745;">Hace {} min</span>', int(delta.seconds / 60))
            elif delta < timedelta(days=1):
                return format_html('<span>Hace {} hr</span>', int(delta.seconds / 3600))
            else:
                return obj.last_used.strftime('%d/%m/%Y')
        return format_html('<span style="color: #999;">Nunca</span>')
    last_used_display.short_description = 'Último Uso'
    
    def created_at_display(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return '-'
    created_at_display.short_description = 'Configurado'
    
    def backup_codes_display(self, obj):
        """Muestra los códigos de backup."""
        if not obj.backup_codes:
            return format_html('<p style="color: #999;">Sin códigos de backup</p>')
        
        html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
        html += '<p style="margin-top: 0;"><strong>Códigos de Backup:</strong></p>'
        html += '<ul style="list-style: none; padding: 0; font-family: monospace;">'
        for code in obj.backup_codes:
            html += f'<li style="padding: 5px; background: white; margin: 3px 0; border-radius: 3px;">{code}</li>'
        html += '</ul>'
        html += '<p style="color: #dc3545; margin-bottom: 0;"><small>⚠️ Estos códigos son de un solo uso</small></p>'
        html += '</div>'
        return format_html(html)
    backup_codes_display.short_description = 'Códigos de Backup'
    
    @admin.action(description='✗ Deshabilitar 2FA')
    def disable_2fa(self, request, queryset):
        """Deshabilita 2FA para usuarios seleccionados."""
        updated = queryset.update(is_enabled=False)
        self.message_user(
            request,
            f'2FA deshabilitado para {updated} usuario(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='🔄 Regenerar códigos backup')
    def regenerate_backup_codes(self, request, queryset):
        """Regenera códigos de backup."""
        from .api.services_advanced import TwoFactorService
        
        count = 0
        for two_factor in queryset:
            new_codes = TwoFactorService.generate_backup_codes()
            two_factor.backup_codes = new_codes
            two_factor.save()
            count += 1
        
        self.message_user(
            request,
            f'Códigos regenerados para {count} usuario(s).',
            messages.SUCCESS
        )
    
    def has_add_permission(self, request):
        return False


# ==============================================================================
# WEBHOOKS ADMIN
# ==============================================================================

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    """Administración de webhooks."""
    
    list_display = [
        'name', 
        'url_display', 
        'is_active_badge', 
        'events_display', 
        'logs_count', 
        'last_delivery',
        'created_at_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['secret', 'created_at', 'updated_at', 'recent_logs']
    
    fieldsets = (
        ('Información', {
            'fields': ('name', 'url', 'is_active')
        }),
        ('Configuración', {
            'fields': ('events', 'secret', 'headers'),
            'description': 'Eventos a escuchar y configuración de seguridad'
        }),
        ('Logs Recientes', {
            'fields': ('recent_logs',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_webhooks', 'deactivate_webhooks', 'test_webhook']
    
    def url_display(self, obj):
        """Muestra la URL acortada."""
        url = obj.url
        if len(url) > 50:
            display = url[:47] + '...'
        else:
            display = url
        return format_html(
            '<a href="{}" target="_blank" style="font-family: monospace;">{}</a>',
            url,
            display
        )
    url_display.short_description = 'URL'
    
    def is_active_badge(self, obj):
        """Badge de estado."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px;">Inactivo</span>'
        )
    is_active_badge.short_description = 'Estado'
    
    def events_display(self, obj):
        """Muestra los eventos."""
        events = obj.events[:3]
        display = ', '.join([f'<code>{e}</code>' for e in events])
        if len(obj.events) > 3:
            display += f' <span style="color: #666;">(+{len(obj.events) - 3})</span>'
        return format_html(display)
    events_display.short_description = 'Eventos'
    
    def logs_count(self, obj):
        """Cuenta de logs."""
        total = obj.logs.count()
        success = obj.logs.filter(success=True).count()
        failed = total - success
        
        return format_html(
            '<div style="font-size: 11px;">'
            '<span style="color: #28a745;">✓ {}</span> / '
            '<span style="color: #dc3545;">✗ {}</span>'
            '</div>',
            success,
            failed
        )
    logs_count.short_description = 'Entregas'
    
    def last_delivery(self, obj):
        """Última entrega."""
        last_log = obj.logs.order_by('-delivered_at').first()
        if last_log:
            delta = timezone.now() - last_log.delivered_at
            if delta < timedelta(hours=1):
                time_str = f'Hace {int(delta.seconds / 60)} min'
            elif delta < timedelta(days=1):
                time_str = f'Hace {int(delta.seconds / 3600)} hr'
            else:
                time_str = last_log.delivered_at.strftime('%d/%m/%Y')
            
            if last_log.success:
                return format_html('<span style="color: #28a745;">✓ {}</span>', time_str)
            else:
                return format_html('<span style="color: #dc3545;">✗ {}</span>', time_str)
        return format_html('<span style="color: #999;">Nunca</span>')
    last_delivery.short_description = 'Última Entrega'
    
    def created_at_display(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return '-'
    created_at_display.short_description = 'Creado'
    
    def recent_logs(self, obj):
        """Logs recientes."""
        logs = obj.logs.order_by('-delivered_at')[:10]
        if not logs:
            return format_html('<p style="color: #999;">Sin logs</p>')
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f8f9fa;"><th>Evento</th><th>Estado</th><th>Fecha</th><th>Respuesta</th></tr>'
        
        for log in logs:
            status = '✓' if log.success else '✗'
            status_color = '#28a745' if log.success else '#dc3545'
            html += f'<tr style="border-bottom: 1px solid #dee2e6;">'
            html += f'<td><code>{log.event_type}</code></td>'
            html += f'<td><span style="color: {status_color}; font-weight: bold;">{status}</span></td>'
            html += f'<td>{log.delivered_at.strftime("%d/%m %H:%M")}</td>'
            html += f'<td>{log.response_status or "N/A"}</td>'
            html += '</tr>'
        
        html += '</table>'
        return format_html(html)
    recent_logs.short_description = 'Logs Recientes'
    
    @admin.action(description='✓ Activar webhooks')
    def activate_webhooks(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} webhook(s) activado(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='✗ Desactivar webhooks')
    def deactivate_webhooks(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} webhook(s) desactivado(s).',
            messages.WARNING
        )
    
    @admin.action(description='🧪 Probar webhook')
    def test_webhook(self, request, queryset):
        """Envía un evento de prueba."""
        from .api.services_advanced import WebhookService
        
        for webhook in queryset:
            test_data = {
                'test': True,
                'message': 'Este es un evento de prueba desde el admin',
                'timestamp': timezone.now().isoformat()
            }
            WebhookService.send_webhook(webhook, 'test.event', test_data)
        
        self.message_user(
            request,
            f'Evento de prueba enviado a {queryset.count()} webhook(s).',
            messages.INFO
        )


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Administración de logs de webhooks."""
    
    list_display = [
        'webhook_link',
        'event_type_badge', 
        'success_badge', 
        'response_status', 
        'attempts', 
        'delivered_at_display'
    ]
    list_filter = ['success', 'event_type', 'delivered_at', 'response_status']
    search_fields = ['webhook__name', 'event_type', 'error_message']
    readonly_fields = [
        'webhook', 
        'event_type', 
        'payload_display', 
        'response_status', 
        'response_body_display', 
        'success', 
        'error_message', 
        'attempts', 
        'delivered_at'
    ]
    ordering = ['-delivered_at']
    date_hierarchy = 'delivered_at'
    
    fieldsets = (
        ('Información', {
            'fields': ('webhook', 'event_type', 'success', 'delivered_at')
        }),
        ('Request', {
            'fields': ('payload_display', 'attempts')
        }),
        ('Response', {
            'fields': ('response_status', 'response_body_display', 'error_message')
        })
    )
    
    actions = ['retry_failed', 'delete_old_logs']
    
    def webhook_link(self, obj):
        """Link al webhook."""
        url = reverse('admin:user_webhook_change', args=[obj.webhook.id])
        return format_html('<a href="{}">{}</a>', url, obj.webhook.name)
    webhook_link.short_description = 'Webhook'
    
    def event_type_badge(self, obj):
        """Badge para tipo de evento."""
        colors = {
            'user.created': '#28a745',
            'user.updated': '#007bff',
            'user.login': '#17a2b8',
            'user.logout': '#6c757d',
            'user.deleted': '#dc3545',
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.event_type
        )
    event_type_badge.short_description = 'Evento'
    
    def success_badge(self, obj):
        """Badge de éxito."""
        if obj.success:
            return format_html(
                '<span style="color: #28a745; font-size: 18px; font-weight: bold;">✓</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 18px; font-weight: bold;">✗</span>'
        )
    success_badge.short_description = 'Estado'
    
    def delivered_at_display(self, obj):
        """Fecha formateada."""
        if obj.delivered_at:
            return obj.delivered_at.strftime('%d/%m/%Y %H:%M:%S')
        return '-'
    delivered_at_display.short_description = 'Entregado'
    
    def payload_display(self, obj):
        """Muestra el payload formateado."""
        if obj.payload:
            payload_json = json.dumps(obj.payload, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; '
                'overflow-x: auto; max-height: 300px;">{}</pre>',
                payload_json
            )
        return format_html('<span style="color: #999;">Sin payload</span>')
    payload_display.short_description = 'Payload'
    
    def response_body_display(self, obj):
        """Muestra la respuesta formateada."""
        if obj.response_body:
            # Intentar parsear como JSON
            try:
                response_json = json.loads(obj.response_body)
                formatted = json.dumps(response_json, indent=2, ensure_ascii=False)
            except:
                formatted = obj.response_body
            
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; '
                'overflow-x: auto; max-height: 300px;">{}</pre>',
                formatted
            )
        return format_html('<span style="color: #999;">Sin respuesta</span>')
    response_body_display.short_description = 'Respuesta'
    
    @admin.action(description='🔄 Reintentar fallidos')
    def retry_failed(self, request, queryset):
        """Reintenta webhooks fallidos."""
        from .api.services_advanced import WebhookService
        
        failed = queryset.filter(success=False, attempts__lt=3)
        count = 0
        
        for log in failed:
            WebhookService.retry_failed_webhook(log.id)
            count += 1
        
        self.message_user(
            request,
            f'{count} webhook(s) reintentado(s).',
            messages.INFO
        )
    
    @admin.action(description='🗑️ Eliminar logs antiguos (>30 días)')
    def delete_old_logs(self, request, queryset):
        """Elimina logs antiguos."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        deleted = queryset.filter(delivered_at__lt=thirty_days_ago).delete()
        self.message_user(
            request,
            f'{deleted[0]} log(s) antiguo(s) eliminado(s).',
            messages.SUCCESS
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==============================================================================
# AUTH LOGS ADMIN
# ==============================================================================

@admin.register(AuthLog)
class AuthLogAdmin(admin.ModelAdmin):
    """Administración de logs de autenticación."""
    
    list_display = [
        'user_link',
        'event_type_badge', 
        'success_badge', 
        'ip_address', 
        'timestamp_display'
    ]
    list_filter = ['event_type', 'success', 'timestamp']
    search_fields = ['user__email', 'ip_address', 'details']
    readonly_fields = [
        'user', 
        'event_type', 
        'ip_address', 
        'user_agent', 
        'success', 
        'details', 
        'timestamp'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información', {
            'fields': ('user', 'event_type', 'success', 'timestamp')
        }),
        ('Detalles Técnicos', {
            'fields': ('ip_address', 'user_agent', 'details')
        })
    )
    
    actions = ['export_logs_csv', 'delete_old_logs']
    
    def user_link(self, obj):
        """Link al usuario."""
        if obj.user:
            url = reverse('admin:user_useraccount_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html('<span style="color: #999;">Anónimo</span>')
    user_link.short_description = 'Usuario'
    
    def event_type_badge(self, obj):
        """Badge para tipo de evento."""
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
        label = obj.event_type.replace('_', ' ').title()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            label
        )
    event_type_badge.short_description = 'Evento'
    
    def success_badge(self, obj):
        """Badge de éxito."""
        if obj.success:
            return format_html(
                '<span style="color: #28a745; font-size: 18px; font-weight: bold;">✓</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 18px; font-weight: bold;">✗</span>'
        )
    success_badge.short_description = '✓'
    
    def timestamp_display(self, obj):
        """Fecha y hora formateada."""
        if obj.timestamp:
            delta = timezone.now() - obj.timestamp
            if delta < timedelta(hours=1):
                return format_html(
                    '<span style="color: #28a745;">Hace {} min</span>',
                    int(delta.seconds / 60)
                )
            elif delta < timedelta(days=1):
                return format_html(
                    'Hace {} hr',
                    int(delta.seconds / 3600)
                )
            else:
                return obj.timestamp.strftime('%d/%m/%Y %H:%M')
        return '-'
    timestamp_display.short_description = 'Cuándo'
    
    @admin.action(description='📥 Exportar a CSV')
    def export_logs_csv(self, request, queryset):
        """Exporta logs a CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="auth_logs.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'Usuario', 'Evento', 'Éxito', 'IP', 'Fecha', 'Detalles'
        ])
        
        for log in queryset:
            writer.writerow([
                log.user.email if log.user else 'Anónimo',
                log.event_type,
                'Sí' if log.success else 'No',
                log.ip_address,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.details
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} log(s) exportado(s).',
            messages.SUCCESS
        )
        return response
    
    @admin.action(description='🗑️ Eliminar logs antiguos (>60 días)')
    def delete_old_logs(self, request, queryset):
        """Elimina logs antiguos."""
        sixty_days_ago = timezone.now() - timedelta(days=60)
        deleted = queryset.filter(timestamp__lt=sixty_days_ago).delete()
        self.message_user(
            request,
            f'{deleted[0]} log(s) antiguo(s) eliminado(s).',
            messages.SUCCESS
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==============================================================================
# USER PROFILE ADMIN
# ==============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de usuario."""
    
    list_display = ['user_link', 'phone', 'bio_preview']
    search_fields = ['user__email', 'phone', 'bio']
    readonly_fields = ['user']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información de Contacto', {
            'fields': ('phone',)
        }),
        ('Biografía', {
            'fields': ('bio',)
        })
    )
    
    def user_link(self, obj):
        """Link al usuario."""
        url = reverse('admin:user_useraccount_change', args=[obj.user.id])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.user.email
        )
    user_link.short_description = 'Usuario'
    
    def bio_preview(self, obj):
        """Preview de la bio."""
        if obj.bio:
            preview = obj.bio[:60] + '...' if len(obj.bio) > 60 else obj.bio
            return preview
        return format_html('<span style="color: #999;">Sin biografía</span>')
    bio_preview.short_description = 'Bio'