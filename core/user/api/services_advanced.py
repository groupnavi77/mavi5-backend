"""
Servicios avanzados: Roles, 2FA, Webhooks
Crear como: core/user/api/services_advanced.py
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hmac
import hashlib
import json
import requests
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from ..models import (
    UserAccount, Role, Permission, 
    TwoFactorAuth, Webhook, WebhookLog
)


# ==============================================================================
# SERVICIO DE ROLES Y PERMISOS
# ==============================================================================

class RoleService:
    """Gestión de roles y permisos."""
    
    @staticmethod
    def create_role(name: str, description: str = "", permissions: List[str] = None) -> Role:
        """Crea un nuevo rol con permisos."""
        role = Role.objects.create(
            name=name,
            description=description
        )
        
        if permissions:
            perm_objects = Permission.objects.filter(code__in=permissions)
            role.permissions.set(perm_objects)
        
        return role
    
    @staticmethod
    def assign_role_to_user(user: UserAccount, role_name: str) -> bool:
        """Asigna un rol a un usuario."""
        try:
            role = Role.objects.get(name=role_name)
            user.roles.add(role)
            return True
        except Role.DoesNotExist:
            return False
    
    @staticmethod
    def remove_role_from_user(user: UserAccount, role_name: str) -> bool:
        """Remueve un rol de un usuario."""
        try:
            role = Role.objects.get(name=role_name)
            user.roles.remove(role)
            return True
        except Role.DoesNotExist:
            return False
    
    @staticmethod
    def user_has_permission(user: UserAccount, permission_code: str) -> bool:
        """Verifica si un usuario tiene un permiso específico."""
        # Superusuarios tienen todos los permisos
        if user.is_superuser:
            return True
        
        # Staff tienen permisos básicos
        if user.is_staff and permission_code.startswith('product.'):
            return True
        
        # Verificar en roles
        return user.roles.filter(
            permissions__code=permission_code
        ).exists()
    
    @staticmethod
    def get_user_permissions(user: UserAccount) -> List[str]:
        """Obtiene todos los permisos de un usuario."""
        if user.is_superuser:
            return list(Permission.objects.values_list('code', flat=True))
        
        return list(
            Permission.objects.filter(
                roles__users=user
            ).distinct().values_list('code', flat=True)
        )
    
    @staticmethod
    def initialize_default_roles():
        """Crea roles por defecto del sistema."""
        # Crear permisos básicos
        perms = [
            ('product.view', 'Ver Productos', 'product'),
            ('product.create', 'Crear Productos', 'product'),
            ('product.edit', 'Editar Productos', 'product'),
            ('product.delete', 'Eliminar Productos', 'product'),
            ('user.view', 'Ver Usuarios', 'user'),
            ('user.edit', 'Editar Usuarios', 'user'),
            ('user.delete', 'Eliminar Usuarios', 'user'),
            ('order.view', 'Ver Órdenes', 'order'),
            ('order.manage', 'Gestionar Órdenes', 'order'),
        ]
        
        for code, name, module in perms:
            Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': module}
            )
        
        # Crear roles
        admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={
                'description': 'Administrador completo',
                'is_system_role': True
            }
        )
        admin_role.permissions.set(Permission.objects.all())
        
        designer_role, _ = Role.objects.get_or_create(
            name='Designer',
            defaults={
                'description': 'Puede crear y editar productos',
                'is_system_role': True
            }
        )
        designer_role.permissions.set(
            Permission.objects.filter(code__in=['product.view', 'product.create', 'product.edit'])
        )
        
        customer_role, _ = Role.objects.get_or_create(
            name='Customer',
            defaults={
                'description': 'Usuario cliente',
                'is_system_role': True
            }
        )
        customer_role.permissions.set(
            Permission.objects.filter(code__in=['product.view', 'order.view'])
        )


# ==============================================================================
# SERVICIO DE 2FA (TWO-FACTOR AUTHENTICATION)
# ==============================================================================

class TwoFactorService:
    """Gestión de autenticación de dos factores."""
    
    @staticmethod
    def generate_secret() -> str:
        """Genera una clave secreta para TOTP."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Genera códigos de respaldo."""
        return [
            secrets.token_hex(4).upper()
            for _ in range(count)
        ]
    
    @staticmethod
    def enable_2fa(user: UserAccount) -> Dict:
        """
        Habilita 2FA para un usuario.
        Retorna el QR code y códigos de respaldo.
        """
        secret = TwoFactorService.generate_secret()
        backup_codes = TwoFactorService.generate_backup_codes()
        
        # Crear o actualizar configuración 2FA
        two_factor, created = TwoFactorAuth.objects.get_or_create(
            user=user,
            defaults={
                'secret_key': secret,
                'backup_codes': backup_codes,
                'is_enabled': False  # Primero debe verificar
            }
        )
        
        if not created:
            two_factor.secret_key = secret
            two_factor.backup_codes = backup_codes
            two_factor.is_enabled = False
            two_factor.save()
        
        # Generar QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=getattr(settings, 'SITE_NAME', 'Avisosya.pe')
        )
        
        # Crear imagen QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'backup_codes': backup_codes,
            'provisioning_uri': provisioning_uri
        }
    
    @staticmethod
    def verify_and_enable_2fa(user: UserAccount, code: str) -> bool:
        """Verifica el código TOTP y habilita 2FA."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            totp = pyotp.TOTP(two_factor.secret_key)
            
            if totp.verify(code, valid_window=1):
                two_factor.is_enabled = True
                two_factor.last_used = timezone.now()
                two_factor.save()
                return True
            
            return False
        except TwoFactorAuth.DoesNotExist:
            return False
    
    @staticmethod
    def verify_2fa_code(user: UserAccount, code: str) -> bool:
        """Verifica un código 2FA durante el login."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=user, is_enabled=True)
            
            # Verificar código TOTP
            totp = pyotp.TOTP(two_factor.secret_key)
            if totp.verify(code, valid_window=1):
                two_factor.last_used = timezone.now()
                two_factor.save()
                return True
            
            # Verificar código de respaldo
            if code.upper() in two_factor.backup_codes:
                # Remover código usado
                two_factor.backup_codes.remove(code.upper())
                two_factor.last_used = timezone.now()
                two_factor.save()
                return True
            
            return False
        except TwoFactorAuth.DoesNotExist:
            return False
    
    @staticmethod
    def disable_2fa(user: UserAccount) -> bool:
        """Deshabilita 2FA para un usuario."""
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            two_factor.is_enabled = False
            two_factor.save()
            return True
        except TwoFactorAuth.DoesNotExist:
            return False
    
    @staticmethod
    def has_2fa_enabled(user: UserAccount) -> bool:
        """Verifica si un usuario tiene 2FA habilitado."""
        try:
            return TwoFactorAuth.objects.get(user=user).is_enabled
        except TwoFactorAuth.DoesNotExist:
            return False


# ==============================================================================
# SERVICIO DE WEBHOOKS
# ==============================================================================

class WebhookService:
    """Gestión de webhooks para eventos."""
    
    @staticmethod
    def trigger_event(event_type: str, data: dict):
        """Dispara webhooks para un evento específico."""
        # ✅ CORRECTO para SQLite - obtén todos y filtra en Python
        webhooks = Webhook.objects.filter(is_active=True)
        
        for webhook in webhooks:
            # Filtra en Python, no en BD
            if event_type in webhook.events:
                WebhookService.send_webhook(webhook, event_type, data)
    
    @staticmethod
    def send_webhook(webhook: Webhook, event_type: str, data: Dict):
        """Envía un webhook específico."""
        payload = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Generar firma HMAC
        signature = WebhookService.generate_signature(
            webhook.secret,
            json.dumps(payload)
        )
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Event-Type': event_type,
        }
        
        # Agregar headers personalizados
        if webhook.headers:
            headers.update(webhook.headers)
        
        # Intentar enviar
        try:
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Registrar log
            WebhookLog.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                response_status=response.status_code,
                response_body=response.text[:1000],  # Limitar tamaño
                success=200 <= response.status_code < 300,
                attempts=1
            )
            
        except Exception as e:
            # Registrar error
            WebhookLog.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                success=False,
                error_message=str(e),
                attempts=1
            )
    
    @staticmethod
    def generate_signature(secret: str, payload: str) -> str:
        """Genera firma HMAC para el webhook."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_signature(secret: str, payload: str, signature: str) -> bool:
        """Verifica la firma de un webhook."""
        expected = WebhookService.generate_signature(secret, payload)
        return hmac.compare_digest(expected, signature)
    
    @staticmethod
    def retry_failed_webhook(log_id: int):
        """Reintenta enviar un webhook fallido."""
        try:
            log = WebhookLog.objects.get(id=log_id)
            if log.attempts >= 3:
                return False  # Máximo 3 intentos
            
            WebhookService.send_webhook(
                log.webhook,
                log.event_type,
                log.payload['data']
            )
            
            log.attempts += 1
            log.save()
            return True
            
        except WebhookLog.DoesNotExist:
            return False


# ==============================================================================
# EVENTOS DE WEBHOOKS
# ==============================================================================

def trigger_user_event(event_type: str, user: UserAccount, extra_data: Dict = None):
    """Helper para disparar eventos de usuario."""
    data = {
        'user_id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_verified': user.is_verified,
    }
    
    if extra_data:
        data.update(extra_data)
    
    WebhookService.trigger_event(event_type, data)