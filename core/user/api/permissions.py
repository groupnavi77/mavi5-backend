from ninja.errors import HttpException
from functools import wraps
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


def token_required(f):
    """
    Decorador para verificar que el usuario esté autenticado con JWT
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            raise HttpException(status_code=401, detail="Token no proporcionado")
        
        token = auth_header.split(' ')[1]
        
        try:
            jwt_authenticator = JWTAuthentication()
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token)
            request.user = user
            
            if not user.is_active:
                raise HttpException(status_code=403, detail="Usuario inactivo")
                
        except (InvalidToken, AuthenticationFailed) as e:
            raise HttpException(status_code=401, detail="Token inválido o expirado")
        
        return f(request, *args, **kwargs)
    
    return decorated_function


def staff_required(f):
    """
    Decorador para verificar que el usuario sea staff
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise HttpException(status_code=401, detail="No autenticado")
        
        if not request.user.is_staff:
            raise HttpException(status_code=403, detail="Permiso denegado. Se requiere acceso staff")
        
        return f(request, *args, **kwargs)
    
    return decorated_function


def superuser_required(f):
    """
    Decorador para verificar que el usuario sea superusuario
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise HttpException(status_code=401, detail="No autenticado")
        
        if not request.user.is_superuser:
            raise HttpException(status_code=403, detail="Permiso denegado. Se requiere acceso de superusuario")
        
        return f(request, *args, **kwargs)
    
    return decorated_function


def verified_email_required(f):
    """
    Decorador para verificar que el email esté verificado
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise HttpException(status_code=401, detail="No autenticado")
        
        if not request.user.is_verified:
            raise HttpException(status_code=403, detail="Email no verificado")
        
        return f(request, *args, **kwargs)
    
    return decorated_function