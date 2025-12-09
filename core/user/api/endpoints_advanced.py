"""
Endpoints avanzados: 2FA, Roles, Webhooks, Dashboard Admin.
Agregar al router principal o crear router separado.
"""

from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from app.auth import jwt_auth
from ..models import UserAccount, Role, Permission, Webhook, AuthLog, TwoFactorAuth
from .schemas_advanced import *
from .services_advanced import RoleService, TwoFactorService, WebhookService, trigger_user_event
from .permissions import require_permissions, get_client_ip, log_auth_event

# Router separado para funcionalidades avanzadas
advanced_router = Router(tags=['Advanced Auth'])

# ==============================================================================
# ENDPOINTS DE 2FA
# ==============================================================================

@advanced_router.post('/2fa/enable', auth=jwt_auth, response=TwoFactorEnableResponseSchema)
def enable_2fa(request):
    """
    Habilita 2FA para el usuario actual.
    Retorna QR code y códigos de respaldo.
    """
    user = request.auth
    
    if TwoFactorService.has_2fa_enabled(user):
        return {
            "success": False,
            "error": "2FA ya está habilitado. Deshabilita primero para regenerar."
        }
    
    result = TwoFactorService.enable_2fa(user)
    
    return {
        "success": True,
        "secret": result['secret'],
        "qr_code": result['qr_code'],
        "backup_codes": result['backup_codes'],
        "message": "Escanea el QR con tu app de autenticación y verifica el código"
    }


@advanced_router.post('/2fa/verify', auth=jwt_auth, response=TwoFactorEnableResponseSchema)
def verify_2fa_setup(request, payload: TwoFactorVerifySchema):
    """
    Verifica el código TOTP y completa la configuración de 2FA.
    """
    user = request.auth
    
    if TwoFactorService.verify_and_enable_2fa(user, payload.code):
        # Disparar webhook
        trigger_user_event('user.2fa_enabled', user)
        
        log_auth_event(
            user=user,
            event_type='2fa_verify',
            ip_address=get_client_ip(request),
            success=True,
            details="2FA habilitado exitosamente"
        )
        
        return {
            "success": True,
            "message": "2FA habilitado exitosamente"
        }
    
    return {
        "success": False,
        "error": "Código inválido"
    }


@advanced_router.post('/2fa/disable', auth=jwt_auth, response=TwoFactorEnableResponseSchema)
def disable_2fa(request, payload: TwoFactorVerifySchema):
    """
    Deshabilita 2FA (requiere verificación).
    """
    user = request.auth
    
    # Verificar código actual antes de deshabilitar
    if not TwoFactorService.verify_2fa_code(user, payload.code):
        return {
            "success": False,
            "error": "Código inválido"
        }
    
    TwoFactorService.disable_2fa(user)
    trigger_user_event('user.2fa_disabled', user)
    
    log_auth_event(
        user=user,
        event_type='2fa_disabled',
        ip_address=get_client_ip(request),
        success=True,
        details="2FA deshabilitado"
    )
    
    return {
        "success": True,
        "message": "2FA deshabilitado"
    }


@advanced_router.get('/2fa/status', auth=jwt_auth, response=TwoFactorStatusSchema)
def get_2fa_status(request):
    """Obtiene el estado de 2FA del usuario actual."""
    user = request.auth
    
    try:
        two_factor = TwoFactorAuth.objects.get(user=user)
        return {
            "enabled": two_factor.is_enabled,
            "last_used": two_factor.last_used
        }
    except TwoFactorAuth.DoesNotExist:
        return {
            "enabled": False,
            "last_used": None
        }


@advanced_router.post('/login-2fa', response={200: dict, 401: dict})
def login_with_2fa(request, payload: LoginWith2FASchema):
    """
    Login con verificación 2FA.
    """
    from .services import UserService
    user_service = UserService()
    
    # Autenticar usuario
    user = user_service.authenticate_user(payload.email, payload.password)
    
    if not user:
        return 401, {"success": False, "error": "Credenciales inválidas"}
    
    # Verificar 2FA si está habilitado
    if TwoFactorService.has_2fa_enabled(user):
        if not TwoFactorService.verify_2fa_code(user, payload.code):
            log_auth_event(
                user=user,
                event_type='2fa_failed',
                ip_address=get_client_ip(request),
                success=False,
                details="Código 2FA inválido"
            )
            return 401, {"success": False, "error": "Código 2FA inválido"}
    
    # Login exitoso
    tokens = user_service.generate_tokens(user)
    
    log_auth_event(
        user=user,
        event_type='login',
        ip_address=get_client_ip(request),
        success=True,
        details="Login con 2FA exitoso"
    )
    
    return 200, {
        "success": True,
        "access": tokens['access'],
        "refresh": tokens['refresh'],
        "user": user_service.get_user_data(user)
    }


# ==============================================================================
# ENDPOINTS DE ROLES (ADMIN)
# ==============================================================================

@advanced_router.get('/roles', auth=jwt_auth, response=List[RoleSchema])
@require_permissions(authenticated=True, staff=True)
def list_roles(request):
    """Lista todos los roles disponibles (solo staff)."""
    roles = Role.objects.prefetch_related('permissions').all()
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "permissions": list(role.permissions.all()),
            "created_at": role.created_at
        }
        for role in roles
    ]


@advanced_router.post('/roles', auth=jwt_auth, response=RoleSchema)
@require_permissions(authenticated=True, staff=True)
def create_role(request, payload: RoleCreateSchema):
    """Crea un nuevo rol (solo staff)."""
    role = RoleService.create_role(
        name=payload.name,
        description=payload.description or "",
        permissions=payload.permission_codes
    )
    
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "permissions": list(role.permissions.all()),
        "created_at": role.created_at
    }


@advanced_router.post('/users/assign-role', auth=jwt_auth, response=dict)
@require_permissions(authenticated=True, staff=True)
def assign_role_to_user(request, payload: AssignRoleSchema):
    """Asigna un rol a un usuario (solo staff)."""
    user = get_object_or_404(UserAccount, id=payload.user_id)
    
    if RoleService.assign_role_to_user(user, payload.role_name):
        return {"success": True, "message": f"Rol {payload.role_name} asignado"}
    
    return {"success": False, "error": "Rol no encontrado"}


@advanced_router.get('/permissions', auth=jwt_auth, response=List[PermissionSchema])
@require_permissions(authenticated=True, staff=True)
def list_permissions(request):
    """Lista todos los permisos disponibles (solo staff)."""
    return list(Permission.objects.all())


# ==============================================================================
# ENDPOINTS DE WEBHOOKS (ADMIN)
# ==============================================================================

@advanced_router.get('/webhooks', auth=jwt_auth, response=List[WebhookSchema])
@require_permissions(authenticated=True, staff=True)
def list_webhooks(request):
    """Lista todos los webhooks (solo staff)."""
    return list(Webhook.objects.all())


@advanced_router.post('/webhooks', auth=jwt_auth, response=WebhookSchema)
@require_permissions(authenticated=True, staff=True)
def create_webhook(request, payload: WebhookCreateSchema):
    """Crea un nuevo webhook (solo staff)."""
    import secrets
    
    webhook = Webhook.objects.create(
        name=payload.name,
        url=payload.url,
        events=payload.events,
        headers=payload.headers,
        secret=secrets.token_hex(32),
        is_active=True
    )
    
    return webhook


@advanced_router.delete('/webhooks/{webhook_id}', auth=jwt_auth, response=dict)
@require_permissions(authenticated=True, staff=True)
def delete_webhook(request, webhook_id: int):
    """Elimina un webhook (solo staff)."""
    webhook = get_object_or_404(Webhook, id=webhook_id)
    webhook.delete()
    return {"success": True, "message": "Webhook eliminado"}


@advanced_router.get('/webhooks/{webhook_id}/logs', auth=jwt_auth, response=List[WebhookLogSchema])
@require_permissions(authenticated=True, staff=True)
def get_webhook_logs(request, webhook_id: int):
    """Obtiene los logs de un webhook (solo staff)."""
    from ..models import WebhookLog
    
    logs = WebhookLog.objects.filter(webhook_id=webhook_id).order_by('-delivered_at')[:50]
    return list(logs)


# ==============================================================================
# DASHBOARD DE ADMINISTRACIÓN
# ==============================================================================

@advanced_router.get('/admin/dashboard', auth=jwt_auth, response=DashboardStatsSchema)
@require_permissions(authenticated=True, staff=True)
def get_dashboard_stats(request):
    """Estadísticas del dashboard (solo staff)."""
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    
    stats = {
        "total_users": UserAccount.objects.count(),
        "verified_users": UserAccount.objects.filter(is_verified=True).count(),
        "active_users_today": AuthLog.objects.filter(
            event_type='login',
            success=True,
            timestamp__date=today
        ).values('user').distinct().count(),
        "failed_logins_today": AuthLog.objects.filter(
            event_type='login_failed',
            timestamp__date=today
        ).count(),
        "users_with_2fa": TwoFactorAuth.objects.filter(is_enabled=True).count(),
        "new_users_this_week": UserAccount.objects.filter(
            created_at__gte=week_ago
        ).count()
    }
    
    return stats


@advanced_router.get('/admin/users', auth=jwt_auth, response=List[UserDetailAdminSchema])
@require_permissions(authenticated=True, staff=True)
def list_users_admin(request, page: int = 1, page_size: int = 20):
    """Lista usuarios con detalles completos (solo staff)."""
    users = UserAccount.objects.prefetch_related('roles').all()
    start = (page - 1) * page_size
    end = start + page_size
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "provider": user.provider,
            "roles": [role.name for role in user.roles.all()],
            "permissions": RoleService.get_user_permissions(user),
            "has_2fa": TwoFactorService.has_2fa_enabled(user),
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        for user in users[start:end]
    ]


@advanced_router.get('/admin/user-activity/{user_id}', auth=jwt_auth, response=UserActivitySchema)
@require_permissions(authenticated=True, staff=True)
def get_user_activity_admin(request, user_id: int):
    """Obtiene actividad detallada de un usuario (solo staff)."""
    user = get_object_or_404(UserAccount, id=user_id)
    
    logs = AuthLog.objects.filter(user=user).order_by('-timestamp')[:20]
    
    return {
        "user_id": user.id,
        "user_email": user.email,
        "total_logins": AuthLog.objects.filter(
            user=user,
            event_type='login',
            success=True
        ).count(),
        "last_login": logs.filter(event_type='login').first().timestamp if logs.filter(event_type='login').exists() else None,
        "failed_attempts": AuthLog.objects.filter(
            user=user,
            event_type='login_failed'
        ).count(),
        "has_2fa": TwoFactorService.has_2fa_enabled(user),
        "recent_activity": [
            {
                "id": log.id,
                "user_email": user.email,
                "event_type": log.event_type,
                "ip_address": log.ip_address,
                "success": log.success,
                "details": log.details,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
    }


@advanced_router.get('/admin/auth-logs', auth=jwt_auth, response=List[AuthLogSchema])
@require_permissions(authenticated=True, staff=True)
def get_auth_logs(request, limit: int = 100):
    """Obtiene logs de autenticación recientes (solo staff)."""
    logs = AuthLog.objects.select_related('user').order_by('-timestamp')[:limit]
    
    return [
        {
            "id": log.id,
            "user_email": log.user.email if log.user else None,
            "event_type": log.event_type,
            "ip_address": log.ip_address,
            "success": log.success,
            "details": log.details,
            "timestamp": log.timestamp
        }
        for log in logs
    ]


# ==============================================================================
# COMANDO DE INICIALIZACIÓN
# ==============================================================================

@advanced_router.post('/admin/initialize-roles', auth=jwt_auth, response=dict)
@require_permissions(authenticated=True, staff=True)
def initialize_default_roles(request):
    """Inicializa roles y permisos por defecto (solo superuser)."""
    if not request.auth.is_superuser:
        return {"success": False, "error": "Solo superusuarios pueden inicializar roles"}
    
    RoleService.initialize_default_roles()
    
    return {
        "success": True,
        "message": "Roles y permisos inicializados correctamente"
    }