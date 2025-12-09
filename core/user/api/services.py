from typing import Optional
from django.utils import timezone
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, timezone as tz
import requests
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, DecodeError , PyJWTError
from ..models import UserAccount, TokenBlacklist
from django.core.mail import send_mail # ⬅️ Nuevo
from django.template.loader import render_to_string # ⬅️ Nuevo


class UserService:
    
    # === GENERACIÓN DE TOKENS (PYJWT PURO) ===
    
    @staticmethod
    def _create_token(user: UserAccount, token_type: str, lifetime: timedelta) -> str:
        now = datetime.now(tz.utc)
        expiration = now + lifetime
        
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': int(expiration.timestamp()),
            'iat': int(now.timestamp()),
            'token_type': token_type,
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def generate_tokens(user: UserAccount):
        # Lee la configuración desde settings.py
        ACCESS_LIFETIME = getattr(settings, 'ACCESS_TOKEN_LIFETIME', timedelta(minutes=15))
        REFRESH_LIFETIME = getattr(settings, 'REFRESH_TOKEN_LIFETIME', timedelta(days=7))

        return {
            "access": UserService._create_token(user, 'access', ACCESS_LIFETIME),
            "refresh": UserService._create_token(user, 'refresh', REFRESH_LIFETIME),
        }
    
# =======================================================
    # 🔑 TOKEN CORE VALIDATION (Función Faltante)
    # =======================================================

    @staticmethod
    def verify_token(token_string: str) -> dict:
        """
        Verifica la firma, expiración y blacklist de CUALQUIER token.
        Retorna el payload decodificado si es válido.
        Lanza una excepción si falla.
        """
        # 1. Chequeo de Blacklist (Control de Revocación)
        if TokenBlacklist.objects.filter(token=token_string).exists():
            # Creamos una excepción genérica para errores de token si no existe InvalidToken
            raise PyJWTError("Token revocado (Blacklisted)")
        
        # 2. Decodificación y Verificación de Firma/Expiración
        try:
            # PyJWT verifica la firma, la expiración ('exp'), etc., por defecto.
            payload = jwt.decode(
                token_string, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            return payload
        except PyJWTError as e:
            # Relanza el error para ser atrapado por el llamador
            raise PyJWTError(f"Token JWT inválido: {e}")
    @staticmethod
    def refresh_access_token(refresh_token_string: str) -> Optional[dict]:
        """
        Valida el Refresh Token antiguo y emite un NUEVO par de tokens.
        """
        try:
            # 1. Validar Token (Verifica firma, expiración Y Blacklist)
            payload = UserService.verify_token(refresh_token_string)
            
            # 2. Obtener el usuario
            user_id = payload.get('user_id')
            user = UserAccount.objects.get(id=user_id)
            
            # 3. Revocar el token antiguo (Seguridad: Lo añadimos a la blacklist)
            # Nota: Esto es solo para tokens deslizantes. Si no quieres deslizar, 
            # podrías saltar este paso.
            UserService.logout_user(refresh_token_string)

            # 4. Generar el NUEVO par de tokens (Access y Refresh)
            new_tokens = UserService.generate_tokens(user)
            
            return new_tokens
            
        except PyJWTError:
            # Captura cualquier error de JWT (firma, expiración, blacklist)
            return None
        except UserAccount.DoesNotExist:
            # Si el usuario en el token no existe
            return None
        except Exception:
            # Para errores inesperados (ej. DB, etc.)
            return None
        
    # === LOGICA DE AUTH Y BLACKLIST ===

    @staticmethod
    def authenticate_user(email: str, password: str):
        try:
            user = UserAccount.objects.get(email__iexact=email)
            if user.check_password(password) and user.is_active:
                return user
            return None
        except UserAccount.DoesNotExist:
            return None

    @staticmethod
    def logout_user(token: str):
        """Añade un token a la blacklist decodificándolo primero."""
        try:
            # verify_exp=False permite revocar tokens que ya expiraron
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            
            if TokenBlacklist.objects.filter(token=token).exists():
                return True

            user_id = decoded.get('user_id')
            user = UserAccount.objects.get(id=user_id)
            exp = decoded.get('exp')
            expires_at = timezone.datetime.fromtimestamp(exp, tz=tz.utc) # O bien, tz.utc si usas la importación de datetime
            
            if not TokenBlacklist.objects.filter(token=token).exists():
                TokenBlacklist.objects.create(
                    token=token,
                    user=user,
                    expires_at=expires_at
                )
            
            return True
        except Exception as e:
            print(f"Error blacklist: {e}")
            return False

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        return TokenBlacklist.objects.filter(token=token).exists()

    @staticmethod
    def get_user_data(user: UserAccount):
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
        }

    # === SOCIAL AUTH LOGIC ===

    @staticmethod
    def get_google_user(access_token: str, id_token: str = None):
        try:
            url = 'https://www.googleapis.com/oauth2/v1/userinfo?access_token='
            response = requests.get(url + access_token)
            if response.status_code != 200: return None
            data = response.json()
            return {
                'email': data.get('email'),
                'first_name': data.get('given_name', ''),
                'last_name': data.get('family_name', ''),
                'provider': 'google',
            }
        except: return None

    @staticmethod
    def get_facebook_user(access_token: str):
        try:
            url = 'https://graph.facebook.com/me?fields=id,email,first_name,last_name&access_token='
            response = requests.get(url + access_token)
            if response.status_code != 200: return None
            data = response.json()
            return {
                'email': data.get('email'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'provider': 'facebook',
            }
        except: return None

    @staticmethod
    def get_github_user(access_token: str):
        try:
            headers = {'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}
            response = requests.get('https://api.github.com/user', headers=headers)
            if response.status_code != 200: return None
            data = response.json()
            
            email = data.get('email')
            if not email: # Fetch private email
                emails_resp = requests.get('https://api.github.com/user/emails', headers=headers)
                if emails_resp.status_code == 200:
                    for e in emails_resp.json():
                        if e.get('primary'): email = e.get('email'); break
            
            return {
                'email': email,
                'first_name': data.get('name', '').split(' ')[0],
                'last_name': ' '.join(data.get('name', '').split(' ')[1:]),
                'provider': 'github',
            }
        except: return None

    @staticmethod
    def create_or_update_social_user(user_data: dict):
        try:
            email = user_data.get('email')
            if not email: return None
            
            user, created = UserAccount.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'is_verified': True,
                    # Solo cambiamos provider si era email puro
                    'provider': user_data.get('provider') 
                }
            )
            # Si se creó recién, setear un password inutilizable
            if created:
                user.set_unusable_password()
                user.save()
                
            return user
        except Exception: return None

# =======================================================
    # 🔑 LÓGICA DE TOKENS DE ACCIÓN (VERIFY / RESET)
    # =======================================================

    @staticmethod
    def _create_action_token(user: UserAccount, action_type: str, lifetime: timedelta) -> str:
        """Crea un JWT para una acción específica (ej: 'verify' o 'reset')."""
        now = datetime.now(tz.utc)
        expiration = now + lifetime
        
        # 💡 CAMBIO CLAVE AQUÍ: Solo llama a .timestamp() si el campo NO es None.
        # Si es None, usa 0 (el timestamp de 1970-01-01), que es seguro.
        last_reset = 0
        if user.last_password_reset:
            last_reset = int(user.last_password_reset.timestamp())
        
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': int(expiration.timestamp()),
            'iat': int(now.timestamp()),
            'action': action_type,
            'lpr': last_reset # <-- Ahora es seguro
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def verify_action_token(token: str, action_type: str):
        """Decodifica y valida el token de acción."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # 1. Verificar tipo de acción (para no usar un token de verificar en reseteo)
            if payload.get('action') != action_type:
                return None
            
            # 2. Obtener usuario
            user_id = payload.get('user_id')
            user = UserAccount.objects.get(id=user_id)
            
            # 3. Seguridad extra para Reset Password:
            # Si el usuario cambió su contraseña DESPUÉS de emitir este token, el token ya no sirve.
            if action_type == 'reset':
                token_lpr = payload.get('lpr', 0)
                user_lpr = int(user.last_password_reset.timestamp()) if user.last_password_reset else 0
                if token_lpr < user_lpr:
                    return None # El token es viejo

            return user
        except (ExpiredSignatureError, InvalidSignatureError, DecodeError, UserAccount.DoesNotExist):
            return None

    # =======================================================
    # 📧 ENVÍO DE CORREOS
    # =======================================================

    @staticmethod
    def send_action_email(user: UserAccount, action: str):
        """Prepara y envía el correo electrónico."""
        
        DOMAIN = getattr(settings, 'DOMAIN', 'localhost:3000') # URL de tu Frontend
        
        if action == 'verify':
            lifetime = timedelta(hours=24)
            subject = "Verifica tu cuenta en Avisosya.pe"
            template = 'email/verification_email.txt'
            path = 'verify-email' # Ruta en tu Frontend
        elif action == 'reset':
            lifetime = timedelta(hours=1)
            subject = "Restablecer contraseña - Avisosya.pe"
            template = 'email/reset_password_email.txt'
            path = 'reset-password' # Ruta en tu Frontend
        else:
            return False

        # Generar token
        token = UserService._create_action_token(user, action, lifetime)
        
        # Crear Link
        link = f"https://{DOMAIN}/{path}?token={token}"
        
        # Renderizar mensaje
        try:
            message = render_to_string(template, {
                'user': user,
                'link': link,
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error enviando email: {e}")
            raise e # Relanzar para que el endpoint devuelva 500 si falla