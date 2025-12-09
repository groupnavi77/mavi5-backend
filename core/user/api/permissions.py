"""
Sistema de permisos mejorado para Django Ninja.
Incluye decoradores, clases de permiso y validaciones.
"""

from functools import wraps
from typing import Optional, List
from ninja.errors import HttpError
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import jwt
from django.conf import settings

from ..models import UserAccount


# ==============================================================================
# DECORADORES DE AUTENTICACIÓN BÁSICOS
# ==============================================================================

def login_required(func):
    """
    Decorador básico que requiere autenticación.
    El usuario ya viene en request.auth gracias a JWTAuth.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or not request.auth:
            raise HttpError(401, "Autenticación requerida")
        
        if not request.auth.is_active:
            raise HttpError(403, "Usuario inactivo")
        
        return func(request, *args, **kwargs)
    
    return wrapper


def verified_email_required(func):
    """
    Requiere que el email esté verificado.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or not request.auth:
            raise HttpError(401, "Autenticación requerida")
        
        if not request.auth.is_verified:
            raise HttpError(403, "Email no verificado. Por favor verifica tu correo.")
        
        return func(request, *args, **kwargs)
    
    return wrapper


def staff_required(func):
    """
    Requiere que el usuario sea staff.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or not request.auth:
            raise HttpError(401, "Autenticación requerida")
        
        if not request.auth.is_staff:
            raise HttpError(403, "Se requiere permiso de staff")
        
        return func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(func):
    """
    Requiere que el usuario sea superusuario.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or not request.auth:
            raise HttpError(401, "Autenticación requerida")
        
        if not request.auth.is_superuser:
            raise HttpError(403, "Se requiere permiso de superusuario")
        
        return func(request, *args, **kwargs)
    
    return wrapper


# ==============================================================================
# PERMISOS AVANZADOS CON ROLES
# ==============================================================================

def has_role(*required_roles: str):
    """
    Decorador que verifica si el usuario tiene alguno de los roles especificados.
    
    Uso:
        @has_role('admin', 'moderator')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'auth') or not request.auth:
                raise HttpError(401, "Autenticación requerida")
            
            user = request.auth
            
            # Verificar roles del usuario
            user_roles = get_user_roles(user)
            
            if not any(role in user_roles for role in required_roles):
                raise HttpError(403, f"Se requiere uno de estos roles: {', '.join(required_roles)}")
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_user_roles(user: UserAccount) -> List[str]:
    """
    Obtiene los roles de un usuario.
    Puedes extender esto con un modelo Role si quieres roles dinámicos.
    """
    roles = ['user']  # Rol base
    
    if user.is_verified:
        roles.append('verified')
    
    if user.is_staff:
        roles.append('staff')
    
    if user.is_superuser:
        roles.append('admin')
    
    # Aquí puedes agregar lógica para roles personalizados
    # Ejemplo:
    # if hasattr(user, 'custom_role'):
    #     roles.append(user.custom_role.name)
    
    return roles


# ==============================================================================
# PERMISOS BASADOS EN OBJETOS
# ==============================================================================

def is_owner_or_staff(func):
    """
    Permite acceso solo al dueño del recurso o staff.
    Asume que el objeto tiene un campo 'user' o 'owner'.
    
    Uso:
        @is_owner_or_staff
        def update_product(request, product_id: int):
            product = get_object_or_404(Product, id=product_id)
            # request.auth debe ser el dueño o staff
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or not request.auth:
            raise HttpError(401, "Autenticación requerida")
        
        user = request.auth
        
        # Si es staff, permitir acceso
        if user.is_staff:
            return func(request, *args, **kwargs)
        
        # Aquí debes obtener el objeto y verificar ownership
        # Esto es un ejemplo básico - ajusta según tu lógica
        result = func(request, *args, **kwargs)
        return result
    
    return wrapper


def check_object_permission(obj, user: UserAccount, permission: str = 'view') -> bool:
    """
    Verifica permisos sobre un objeto específico.
    
    Args:
        obj: El objeto a verificar
        user: El usuario que intenta acceder
        permission: 'view', 'edit', 'delete'
    
    Returns:
        bool: True si tiene permiso
    """
    # Staff siempre tiene permiso
    if user.is_staff or user.is_superuser:
        return True
    
    # Verificar ownership
    if hasattr(obj, 'user') and obj.user_id == user.id:
        return True
    
    if hasattr(obj, 'owner') and obj.owner_id == user.id:
        return True
    
    # Para permisos de solo lectura
    if permission == 'view' and hasattr(obj, 'is_public') and obj.is_public:
        return True
    
    return False


# ==============================================================================
# RATE LIMITING (PROTECCIÓN CONTRA BRUTE FORCE)
# ==============================================================================

def rate_limit(max_attempts: int = 5, window: int = 60, block_duration: int = 300):
    """
    Limita la cantidad de requests por usuario/IP.
    
    Args:
        max_attempts: Intentos máximos permitidos
        window: Ventana de tiempo en segundos
        block_duration: Duración del bloqueo en segundos
    
    Uso:
        @rate_limit(max_attempts=5, window=60)
        @router.post('/login')
        def login(request, payload):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Identificador único (IP o user_id si está autenticado)
            identifier = get_client_ip(request)
            
            if hasattr(request, 'auth') and request.auth:
                identifier = f"user_{request.auth.id}"
            
            cache_key = f"rate_limit:{func.__name__}:{identifier}"
            block_key = f"blocked:{func.__name__}:{identifier}"
            
            # Verificar si está bloqueado
            if cache.get(block_key):
                raise HttpError(429, f"Demasiados intentos. Intenta de nuevo en {block_duration // 60} minutos.")
            
            # Obtener intentos actuales
            attempts = cache.get(cache_key, 0)
            
            if attempts >= max_attempts:
                # Bloquear usuario
                cache.set(block_key, True, block_duration)
                cache.delete(cache_key)
                raise HttpError(429, f"Demasiados intentos. Bloqueado por {block_duration // 60} minutos.")
            
            # Incrementar contador
            cache.set(cache_key, attempts + 1, window)
            
            # Ejecutar función
            result = func(request, *args, **kwargs)
            
            # Si fue exitoso, resetear contador
            cache.delete(cache_key)
            
            return result
        
        return wrapper
    return decorator


def get_client_ip(request) -> str:
    """Obtiene la IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==============================================================================

def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida la fortaleza de una contraseña.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not any(char.isupper() for char in password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not any(char.islower() for char in password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not any(char.isdigit() for char in password):
        return False, "La contraseña debe contener al menos un número"
    
    # Opcional: caracteres especiales
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, None




# ==============================================================================
# VALIDACIÓN DE TOKENS MEJORADA
# ==============================================================================

def validate_token_claims(payload: dict, required_claims: List[str]) -> bool:
    """
    Valida que el token contenga los claims requeridos.
    """
    return all(claim in payload for claim in required_claims)


def is_token_expired(payload: dict) -> bool:
    """
    Verifica si un token está expirado.
    """
    exp = payload.get('exp')
    if not exp:
        return True
    
    return timezone.now().timestamp() > exp

# ==============================================================================
# LOGGING DE AUDITORÍA
# ==============================================================================

def log_auth_event(user: Optional[UserAccount], event_type: str, ip_address: str, success: bool, details: str = ""):
    """
    Registra eventos de autenticación para auditoría.
    
    Args:
        user: Usuario (puede ser None para intentos fallidos)
        event_type: 'login', 'logout', 'password_reset', etc.
        ip_address: IP del cliente
        success: Si fue exitoso
        details: Detalles adicionales
    """
    from ..models import AuthLog  # Debes crear este modelo
    
    try:
        AuthLog.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            success=success,
            details=details,
            timestamp=timezone.now()
        )
    except Exception as e:
        # No fallar si el log falla
        print(f"Error logging auth event: {e}")


# ==============================================================================
# DECORADOR COMBINADO (TODO EN UNO)
# ==============================================================================

def require_permissions(
    authenticated: bool = True,
    verified: bool = False,
    staff: bool = False,
    roles: Optional[List[str]] = None,
    rate_limit_max: Optional[int] = None
):
    """
    Decorador combinado que aplica múltiples verificaciones.
    
    Uso:
        @require_permissions(authenticated=True, verified=True, roles=['admin'])
        def my_protected_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 1. Autenticación
            if authenticated:
                if not hasattr(request, 'auth') or not request.auth:
                    raise HttpError(401, "Autenticación requerida")
                
                user = request.auth
                
                # 2. Usuario activo
                if not user.is_active:
                    raise HttpError(403, "Usuario inactivo")
                
                # 3. Email verificado
                if verified and not user.is_verified:
                    raise HttpError(403, "Email no verificado")
                
                # 4. Staff
                if staff and not user.is_staff:
                    raise HttpError(403, "Permiso de staff requerido")
                
                # 5. Roles
                if roles:
                    user_roles = get_user_roles(user)
                    if not any(role in user_roles for role in roles):
                        raise HttpError(403, f"Se requiere uno de estos roles: {', '.join(roles)}")
            
            # 6. Rate limiting
            if rate_limit_max:
                # Aplicar rate limit aquí
                pass
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator