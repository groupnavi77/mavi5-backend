# core/user/api/endpoints.py - VERSIÓN COMPLETA Y MEJORADA

from ninja import Router
from ninja.errors import HttpError
from django.conf import settings
from django.utils.timezone import now

from app.auth import jwt_auth
from ..models import UserAccount
from .schemas import (
    LoginSchema, TokenResponseSchema, RefreshTokenSchema,
    UserCreateSchema, SocialAuthSchema, LogoutSchema,
    UserUpdateSchema, PasswordResetConfirmSchema, EmailRequestSchema, 
    EmailVerifyConfirmSchema, PasswordChangeSchema
)
from .services import UserService
from .permissions import (
    rate_limit, 
    get_client_ip, 
    log_auth_event,
    validate_password_strength,
    verified_email_required,
    require_permissions
)

router = Router(tags=['Auth'])
user_service = UserService()

# ===================================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# ===================================================

@router.post('/login', response={200: TokenResponseSchema, 401: TokenResponseSchema, 403: TokenResponseSchema, 429: TokenResponseSchema})
@rate_limit(max_attempts=5, window=300, block_duration=900)  # 5 intentos en 5 min, bloqueo de 15 min
def login(request, payload: LoginSchema):
    """
    Login de usuario con rate limiting.
    - Máximo 5 intentos cada 5 minutos
    - Bloqueo de 15 minutos si se excede
    """
    ip_address = get_client_ip(request)
    user = user_service.authenticate_user(payload.email, payload.password)
    
    if not user:
        # Log de intento fallido
        log_auth_event(
            user=None,
            event_type='login_failed',
            ip_address=ip_address,
            success=False,
            details=f"Email: {payload.email}"
        )
        return 401, {"success": False, "error": "Credenciales inválidas"}
    
    if not user.is_active:
        log_auth_event(
            user=user,
            event_type='login_failed',
            ip_address=ip_address,
            success=False,
            details="Usuario inactivo"
        )
        return 403, {"success": False, "error": "Usuario inactivo"}
    
    # Login exitoso
    tokens = user_service.generate_tokens(user)
    
    log_auth_event(
        user=user,
        event_type='login',
        ip_address=ip_address,
        success=True,
        details="Login exitoso"
    )
    
    # Disparar webhook (si está implementado)
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.login', user, {'ip_address': ip_address})
    except:
        pass
    
    return 200, {
        "success": True,
        "access": tokens['access'],
        "refresh": tokens['refresh'],
        "user": user_service.get_user_data(user)
    }


@router.post('/register', response={200: TokenResponseSchema, 400: TokenResponseSchema})
@rate_limit(max_attempts=3, window=3600)  # 3 registros por hora por IP
def register(request, payload: UserCreateSchema):
    """
    Registro de nuevo usuario con validación de contraseña.
    """
    ip_address = get_client_ip(request)
    
    # Validar email existente
    if UserAccount.objects.filter(email=payload.email).exists():
        return 400, {"success": False, "error": "Email ya registrado"}
    
    # Validar fortaleza de contraseña
    is_valid, error_msg = validate_password_strength(payload.password)
    if not is_valid:
        return 400, {"success": False, "error": error_msg}
    
    try:
        user = UserAccount.objects.create_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_verified=False,
            provider='email'
        )
        
        # Enviar email de verificación
        try:
            user_service.send_action_email(user, 'verify')
        except Exception as e:
            print(f"Error enviando email de verificación: {e}")
        
        tokens = user_service.generate_tokens(user)
        
        log_auth_event(
            user=user,
            event_type='register',
            ip_address=ip_address,
            success=True,
            details="Registro exitoso"
        )
        
        # Disparar webhook
        try:
            from .services_advanced import trigger_user_event
            trigger_user_event('user.created', user)
        except:
            pass
        
        return 200, {
            "success": True,
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": user_service.get_user_data(user),
            "message": "Registro exitoso. Por favor verifica tu email."
        }
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


@router.post('/refresh', response={200: TokenResponseSchema, 401: TokenResponseSchema})
@rate_limit(max_attempts=10, window=60)  # 10 refresh por minuto
def refresh_token(request, payload: RefreshTokenSchema):
    """Renueva el Access Token y el Refresh Token."""
    ip_address = get_client_ip(request)
    
    new_tokens = user_service.refresh_access_token(payload.refresh)
    
    if not new_tokens:
        log_auth_event(
            user=None,
            event_type='token_refresh',
            ip_address=ip_address,
            success=False,
            details="Refresh token inválido"
        )
        return 401, {"success": False, "error": "Refresh Token inválido o revocado"}
    
    return 200, {
        "success": True,
        "access": new_tokens['access'],
        "refresh": new_tokens['refresh']
    }


@router.post('/social-auth', response={200: TokenResponseSchema, 400: TokenResponseSchema, 401: TokenResponseSchema})
@rate_limit(max_attempts=5, window=300)
def social_auth(request, payload: SocialAuthSchema):
    """Autenticación con redes sociales (Google, Facebook, GitHub)."""
    ip_address = get_client_ip(request)
    provider = payload.provider.lower()
    user_data = None
    
    if provider == 'google':
        user_data = user_service.get_google_user(payload.access_token, payload.id_token)
    elif provider == 'facebook':
        user_data = user_service.get_facebook_user(payload.access_token)
    elif provider == 'github':
        user_data = user_service.get_github_user(payload.access_token)
    
    if not user_data:
        return 401, {"success": False, "error": f"Fallo autenticación con {provider}"}
    
    user = user_service.create_or_update_social_user(user_data)
    if not user:
        return 400, {"success": False, "error": "Error al procesar usuario"}
    
    tokens = user_service.generate_tokens(user)
    
    log_auth_event(
        user=user,
        event_type='login',
        ip_address=ip_address,
        success=True,
        details=f"Social auth: {provider}"
    )
    
    # Disparar webhook
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.login', user, {'provider': provider})
    except:
        pass
    
    return 200, {
        "success": True,
        "access": tokens['access'],
        "refresh": tokens['refresh'],
        "user": user_service.get_user_data(user)
    }


# ===================================================
# ENDPOINTS PROTEGIDOS (Requieren autenticación)
# ===================================================

@router.post('/logout', auth=jwt_auth, response={200: TokenResponseSchema})
def logout(request, payload: LogoutSchema):
    """Cierre de sesión con revocación de tokens."""
    ip_address = get_client_ip(request)
    
    user_service.logout_user(payload.access)
    user_service.logout_user(payload.refresh)
    
    log_auth_event(
        user=request.auth,
        event_type='logout',
        ip_address=ip_address,
        success=True,
        details="Logout exitoso"
    )
    
    # Disparar webhook
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.logout', request.auth)
    except:
        pass
    
    return 200, {"success": True, "message": "Sesión cerrada"}


@router.get('/me', auth=jwt_auth, response=TokenResponseSchema)
def get_current_user(request):
    """Obtiene información del usuario actual."""
    return {"success": True, "user": user_service.get_user_data(request.auth)}


@router.put('/me', auth=jwt_auth, response={200: TokenResponseSchema, 400: TokenResponseSchema})
def update_user(request, payload: UserUpdateSchema):
    """Actualiza información del usuario."""
    user = request.auth
    
    if payload.email and payload.email != user.email:
        if UserAccount.objects.filter(email=payload.email).exists():
            return 400, {"success": False, "error": "Email en uso"}
        
        # Si cambia el email, marcar como no verificado
        user.email = payload.email
        user.is_verified = False
        
        # Enviar nuevo email de verificación
        try:
            user_service.send_action_email(user, 'verify')
        except:
            pass
    
    if payload.first_name:
        user.first_name = payload.first_name
    if payload.last_name:
        user.last_name = payload.last_name
    
    user.save()
    
    # Disparar webhook
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.updated', user)
    except:
        pass
    
    return 200, {"success": True, "user": user_service.get_user_data(user)}


@router.post('/change-password', auth=jwt_auth, response={200: TokenResponseSchema, 400: TokenResponseSchema})
def change_password(request, payload: PasswordChangeSchema):
    """Cambio de contraseña (requiere contraseña actual)."""
    user = request.auth
    ip_address = get_client_ip(request)
    
    # Verificar contraseña actual
    if not user.check_password(payload.old_password):
        log_auth_event(
            user=user,
            event_type='password_change',
            ip_address=ip_address,
            success=False,
            details="Contraseña actual incorrecta"
        )
        return 400, {"success": False, "error": "Contraseña actual incorrecta"}
    
    # Validar nueva contraseña
    is_valid, error_msg = validate_password_strength(payload.new_password)
    if not is_valid:
        return 400, {"success": False, "error": error_msg}
    
    # Cambiar contraseña
    user.set_password(payload.new_password)
    user.last_password_reset = now()
    user.save()
    
    log_auth_event(
        user=user,
        event_type='password_change',
        ip_address=ip_address,
        success=True,
        details="Contraseña cambiada exitosamente"
    )
    
    return 200, {"success": True, "message": "Contraseña actualizada"}


# ===================================================
# VERIFICACIÓN DE EMAIL
# ===================================================

@router.post('/request-verification', response={200: TokenResponseSchema, 400: TokenResponseSchema, 500: TokenResponseSchema})
@rate_limit(max_attempts=3, window=3600)  # 3 solicitudes por hora
def request_verification(request, payload: EmailRequestSchema):
    """Solicita un nuevo email de verificación."""
    try:
        user = UserAccount.objects.get(email__iexact=payload.email)
        if user.is_verified:
            return 400, {"success": False, "error": "Cuenta ya verificada"}
        
        user_service.send_action_email(user, 'verify')
        return 200, {"success": True, "message": "Email de verificación enviado"}
    except UserAccount.DoesNotExist:
        # Por seguridad, no revelar si el email existe
        return 200, {"success": True, "message": "Email de verificación enviado"}
    except Exception as e:
        return 500, {"success": False, "error": "Error al enviar email"}


@router.post('/verify-email', response={200: TokenResponseSchema, 400: TokenResponseSchema})
def verify_email(request, payload: EmailVerifyConfirmSchema):
    """Verifica el email del usuario."""
    ip_address = get_client_ip(request)
    user = user_service.verify_action_token(payload.token, 'verify')
    
    if not user:
        return 400, {"success": False, "error": "Token inválido o expirado"}
    
    if user.is_verified:
        return 400, {"success": False, "error": "Email ya verificado"}
    
    user.is_verified = True
    user.save()
    
    log_auth_event(
        user=user,
        event_type='email_verify',
        ip_address=ip_address,
        success=True,
        details="Email verificado"
    )
    
    # Disparar webhook
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.email_verified', user)
    except:
        pass
    
    return 200, {"success": True, "message": "Email verificado con éxito"}


# ===================================================
# RECUPERACIÓN DE CONTRASEÑA
# ===================================================

@router.post('/request-password-reset', response={200: TokenResponseSchema, 500: TokenResponseSchema})
@rate_limit(max_attempts=3, window=3600)  # 3 solicitudes por hora
def request_password_reset(request, payload: EmailRequestSchema):
    """Solicita un email para cambiar la contraseña."""
    try:
        user = UserAccount.objects.get(email__iexact=payload.email)
        user_service.send_action_email(user, 'reset')
        return 200, {"success": True, "message": "Se ha enviado el enlace de recuperación"}
    except UserAccount.DoesNotExist:
        # Por seguridad, no revelar si el email existe
        return 200, {"success": True, "message": "Se ha enviado el enlace de recuperación"}
    except Exception as e:
        return 500, {"success": False, "error": "No se pudo enviar el correo"}


@router.post('/confirm-password-reset', response={200: TokenResponseSchema, 400: TokenResponseSchema})
def confirm_password_reset(request, payload: PasswordResetConfirmSchema):
    """Confirma el cambio de contraseña con token."""
    ip_address = get_client_ip(request)
    user = user_service.verify_action_token(payload.token, 'reset')
    
    if not user:
        return 400, {"success": False, "error": "Token inválido o expirado"}
    
    # Validar nueva contraseña
    is_valid, error_msg = validate_password_strength(payload.new_password)
    if not is_valid:
        return 400, {"success": False, "error": error_msg}
    
    # Cambiar contraseña
    user.set_password(payload.new_password)
    user.last_password_reset = now()
    user.save()
    
    log_auth_event(
        user=user,
        event_type='password_reset',
        ip_address=ip_address,
        success=True,
        details="Contraseña reseteada"
    )
    
    # Disparar webhook
    try:
        from .services_advanced import trigger_user_event
        trigger_user_event('user.password_reset', user)
    except:
        pass
    
    # Auto-login
    tokens = user_service.generate_tokens(user)
    
    return 200, {
        "success": True,
        "message": "Contraseña actualizada",
        "access": tokens['access'],
        "refresh": tokens['refresh']
    }


# ===================================================
# ENDPOINTS ADMINISTRATIVOS (Requieren staff)
# ===================================================

@router.get('/admin/user-activity/{user_id}', auth=jwt_auth, response=dict)
@require_permissions(authenticated=True, staff=True)
def get_user_activity(request, user_id: int):
    """
    Obtiene el historial de actividad de un usuario (solo staff).
    """
    from ..models import AuthLog
    
    user = UserAccount.objects.get(id=user_id)
    logs = AuthLog.objects.filter(user_id=user_id).order_by('-timestamp')[:50]
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        },
        "logs": [
            {
                "event_type": log.event_type,
                "ip_address": log.ip_address,
                "success": log.success,
                "details": log.details,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }