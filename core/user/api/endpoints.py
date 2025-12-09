from time import timezone
from ninja import Router
from ninja.errors import HttpError
from django.conf import settings
from django.utils.timezone import now
from datetime import datetime, timezone as tz
import jwt

from app.auth import jwt_auth
from ..models import UserAccount
from .schemas import (
    LoginSchema, TokenResponseSchema, RefreshTokenSchema,
    UserCreateSchema, SocialAuthSchema, LogoutSchema,
    UserUpdateSchema, PasswordResetConfirmSchema , EmailRequestSchema, EmailVerifyConfirmSchema
)
from .services import UserService

router = Router(tags=['Auth'])
user_service = UserService()

# ===================================================
# ENDPOINTS PÚBLICOS (Login, Register, Refresh, Social)
# ===================================================

@router.post('/login', response={200: TokenResponseSchema, 401: TokenResponseSchema, 403: TokenResponseSchema})
def login(request, payload: LoginSchema):
    user = user_service.authenticate_user(payload.email, payload.password)
    
    if not user:
        return 401, {"success": False, "error": "Credenciales inválidas"}
    if not user.is_active:
        return 403, {"success": False, "error": "Usuario inactivo"}
    
    tokens = user_service.generate_tokens(user)
    return 200, {
        "success": True, 
        "access": tokens['access'], 
        "refresh": tokens['refresh'], 
        "user": user_service.get_user_data(user)
    }

@router.post('/register', response={200: TokenResponseSchema, 400: TokenResponseSchema})
def register(request, payload: UserCreateSchema):
    if UserAccount.objects.filter(email=payload.email).exists():
        return 400, {"success": False, "error": "Email ya registrado"}
    
    try:
        user = UserAccount.objects.create_user(
            email=payload.email, 
            password=payload.password,
            first_name=payload.first_name, 
            last_name=payload.last_name,
            is_verified=False,
            provider='email'
        )
        tokens = user_service.generate_tokens(user)
        return 200, {
            "success": True, 
            "access": tokens['access'], 
            "refresh": tokens['refresh'], 
            "user": user_service.get_user_data(user)
        }
    except Exception as e:
        return 400, {"success": False, "error": str(e)}

@router.post('/refresh', response={200: TokenResponseSchema, 401: TokenResponseSchema})
def refresh_token(request, payload: RefreshTokenSchema):
    """
    Renueva el Access Token y el Refresh Token (Sliding Token).
    """
    
    new_tokens = user_service.refresh_access_token(payload.refresh)
    
    if not new_tokens:
        return 401, {"success": False, "error": "Refresh Token inválido o revocado"}

    # Si fue exitoso, new_tokens ya contiene el nuevo Access y el nuevo Refresh
    return 200, {
        "success": True, 
        "access": new_tokens['access'], 
        "refresh": new_tokens['refresh']
    }

@router.post('/social-auth', response={200: TokenResponseSchema, 400: TokenResponseSchema, 401: TokenResponseSchema})
def social_auth(request, payload: SocialAuthSchema):
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
    return 200, {
        "success": True, 
        "access": tokens['access'], 
        "refresh": tokens['refresh'], 
        "user": user_service.get_user_data(user)
    }

# ===================================================
# ENDPOINTS PROTEGIDOS (Logout, Me)
# ===================================================

@router.post('/logout', auth=jwt_auth, response={200: TokenResponseSchema})
def logout(request, payload: LogoutSchema):
    user_service.logout_user(payload.access)
    user_service.logout_user(payload.refresh)
    return 200, {"success": True, "message": "Sesión cerrada"}

@router.get('/me', auth=jwt_auth, response=TokenResponseSchema)
def get_current_user(request):
    return {"success": True, "user": user_service.get_user_data(request.auth)}

@router.put('/me', auth=jwt_auth, response={200: TokenResponseSchema, 400: TokenResponseSchema})
def update_user(request, payload: UserUpdateSchema):
    user = request.auth
    # Lógica simple de actualización
    if payload.email and payload.email != user.email:
        if UserAccount.objects.filter(email=payload.email).exists():
            return 400, {"success": False, "error": "Email en uso"}
        user.email = payload.email
    
    if payload.first_name: user.first_name = payload.first_name
    if payload.last_name: user.last_name = payload.last_name
    user.save()
    
    return 200, {"success": True, "user": user_service.get_user_data(user)}

# ==========================================
# 📧 VERIFICACIÓN DE EMAIL
# ==========================================

@router.post('/request-verification', response={200: TokenResponseSchema, 400: TokenResponseSchema, 500: TokenResponseSchema})
def request_verification(request, payload: EmailRequestSchema):
    try:
        user = UserAccount.objects.get(email__iexact=payload.email)
        if user.is_verified:
            return 400, {"success": False, "error": "Cuenta ya verificada"}
        
        user_service.send_action_email(user, 'verify')
        return 200, {"success": True, "message": "Email enviado"}
    except UserAccount.DoesNotExist:
        # No revelar si el email existe o no
        return 200, {"success": True, "message": "Email enviado"}
    except Exception as e:
        return 500, {"success": False, "error": f"Error interno: {str(e)}"}

@router.post('/verify-email', response={200: TokenResponseSchema, 400: TokenResponseSchema})
def verify_email(request, payload: EmailVerifyConfirmSchema):
    user = user_service.verify_action_token(payload.token, 'verify')
    
    if not user:
        return 400, {"success": False, "error": "Token inválido o expirado"}
    
    if user.is_verified:
        return 400, {"success": False, "error": "Ya verificado"}
    
    user.is_verified = True
    user.save()
    return 200, {"success": True, "message": "Email verificado con éxito"}

# ==========================================
# 🔑 RECUPERACIÓN DE CONTRASEÑA
# ==========================================

@router.post('/request-password-reset', response={200: TokenResponseSchema, 500: TokenResponseSchema})
def request_password_reset(request, payload: EmailRequestSchema):
    """
    Solicita un email para cambiar la contraseña.
    Si falla el envío, devuelve 500 (ahora permitido en el schema).
    """
    try:
        user = UserAccount.objects.get(email__iexact=payload.email)
        user_service.send_action_email(user, 'reset')
        return 200, {"success": True, "message": "Se ha enviado el enlace de recuperación"}
    except UserAccount.DoesNotExist:
        # Respondemos OK por seguridad para evitar enumeración de usuarios
        return 200, {"success": True, "message": "Se ha enviado el enlace de recuperación"}
    except Exception as e:
        # Capturamos errores de SMTP/Templates
        return 500, {"success": False, "error": "No se pudo enviar el correo"}

@router.post('/confirm-password-reset', response={200: TokenResponseSchema, 400: TokenResponseSchema})
def confirm_password_reset(request, payload: PasswordResetConfirmSchema):
    user = user_service.verify_action_token(payload.token, 'reset')
    
    if not user:
        return 400, {"success": False, "error": "Token inválido o expirado"}
    
    # Cambiar contraseña
    user.set_password(payload.new_password)
    user.last_password_reset = now() # Invalidar tokens anteriores
    user.save()
    
    # Opcional: Auto-login
    tokens = user_service.generate_tokens(user)
    
    return 200, {
        "success": True, 
        "message": "Contraseña actualizada",
        "access": tokens['access'],
        "refresh": tokens['refresh']
    }