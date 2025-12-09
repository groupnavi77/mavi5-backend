import jwt
from ninja.security import HttpBearer
from ninja.errors import HttpError
from django.conf import settings
from django.contrib.auth import get_user_model
from core.user.models import TokenBlacklist # Ajusta la ruta si tu modelo está en otro lado
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, DecodeError

User = get_user_model()

class JWTAuth(HttpBearer):
    """
    Autenticación JWT personalizada usando PyJWT.
    Valida firma, expiración y blacklist.
    """
    def authenticate(self, request, token):
        try:
            # 1. Decodificar Token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            user_id = payload.get('user_id')
            
            if not user_id:
                raise HttpError(401, "Token inválido (Payload incompleto)")

            # 2. Verificar si está en Blacklist
            if TokenBlacklist.objects.filter(token=token).exists():
                raise HttpError(401, "Token revocado (Sesión cerrada)")

            # 3. Obtener Usuario
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise HttpError(401, "Usuario no encontrado")

            # 4. Verificar estado activo
            if not user.is_active:
                raise HttpError(403, "Usuario inactivo")
            
            return user
            
        except ExpiredSignatureError:
            raise HttpError(401, "Token expirado")
        except (InvalidSignatureError, DecodeError):
            raise HttpError(401, "Token inválido")
        except Exception:
            raise HttpError(401, "Error de autenticación")

jwt_auth = JWTAuth()