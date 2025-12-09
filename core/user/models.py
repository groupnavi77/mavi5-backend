from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user
# ==============================================================================
# SISTEMA DE ROLES DINÁMICOS
# ==============================================================================

class Permission(models.Model):
    """
    Permisos granulares del sistema.
    Ejemplos: 'product.create', 'product.edit', 'user.delete'
    """
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Código del permiso (ej: product.create)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Nombre descriptivo"
    )
    description = models.TextField(blank=True)
    module = models.CharField(
        max_length=50,
        help_text="Módulo al que pertenece (ej: product, user, order)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['module', 'code']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
    
    def __str__(self):
        return f"{self.module}.{self.code}"


class Role(models.Model):
    """
    Roles del sistema con permisos asociados.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nombre del rol (ej: Admin, Moderator, Designer)"
    )
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True
    )
    is_system_role = models.BooleanField(
        default=False,
        help_text="Roles del sistema no se pueden eliminar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission_code: str) -> bool:
        """Verifica si el rol tiene un permiso específico"""
        return self.permissions.filter(code=permission_code).exists()

class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    roles = models.ManyToManyField(
    Role,
    related_name='users',
    blank=True,
    help_text="Roles asignados al usuario"
)


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_password_reset = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(
        max_length=50,
        blank=True,
        default='email',
        choices=[
            ('email', 'Email'),
            ('google', 'Google'),
            ('facebook', 'Facebook'),
            ('github', 'GitHub'),
        ],
        verbose_name="Proveedor de autenticación"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Email verificado"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = 'user_account'

    def __str__(self):
        return self.email
    # Métodos helper para roles
    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name=role_name).exists()

    def has_permission(self, permission_code: str) -> bool:
        # Staff y superuser tienen todos los permisos
        if self.is_staff or self.is_superuser:
            return True
        
        # Verificar en roles asignados
        return self.roles.filter(
            permissions__code=permission_code
        ).exists()

    def get_all_permissions(self) -> list:
        if self.is_superuser:
            return Permission.objects.all().values_list('code', flat=True)
        
        return Permission.objects.filter(
            roles__users=self
        ).distinct().values_list('code', flat=True)
    
class UserProfile(models.Model):
    
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    phone = models.CharField(blank=True, max_length=20)
    bio= models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.user.name
    
import uuid

# ...existing UserAccount model...

class TokenBlacklist(models.Model):
    """
    Modelo para mantener tokens en blacklist
    """
    token = models.TextField()  # El string largo del JWT
    expires_at = models.DateTimeField() # ¿Cuándo expira este token naturalmente?
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='blacklisted_tokens')

    def __str__(self):
        return f"Token blacklisted for {self.user.email}"
    




# ==============================================================================
# TWO-FACTOR AUTHENTICATION (2FA)
# ==============================================================================

class TwoFactorAuth(models.Model):
    """
    Configuración de 2FA para usuarios.
    """
    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='two_factor'
    )
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(
        max_length=32,
        help_text="Secret key para TOTP"
    )
    backup_codes = models.JSONField(
        default=list,
        help_text="Códigos de respaldo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Autenticación de Dos Factores'
        verbose_name_plural = 'Autenticaciones de Dos Factores'
    
    def __str__(self):
        status = "Activo" if self.is_enabled else "Inactivo"
        return f"2FA {self.user.email} - {status}"


# ==============================================================================
# WEBHOOKS DE EVENTOS
# ==============================================================================

class Webhook(models.Model):
    """
    Webhooks para notificar eventos de autenticación.
    """
    EVENT_CHOICES = [
        ('user.created', 'Usuario Creado'),
        ('user.updated', 'Usuario Actualizado'),
        ('user.deleted', 'Usuario Eliminado'),
        ('user.login', 'Login Exitoso'),
        ('user.logout', 'Logout'),
        ('user.password_reset', 'Contraseña Reseteada'),
        ('user.email_verified', 'Email Verificado'),
        ('user.2fa_enabled', '2FA Habilitado'),
        ('user.2fa_disabled', '2FA Deshabilitado'),
    ]
    
    name = models.CharField(max_length=200)
    url = models.URLField(help_text="URL donde enviar los eventos")
    events = models.JSONField(
        default=list,
        help_text="Lista de eventos que debe escuchar"
    )
    secret = models.CharField(
        max_length=64,
        help_text="Secret para firmar los webhooks"
    )
    is_active = models.BooleanField(default=True)
    
    # Headers personalizados (opcional)
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Headers adicionales para enviar"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'
    
    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookLog(models.Model):
    """
    Registro de entregas de webhooks.
    """
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    response_status = models.IntegerField(null=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    attempts = models.IntegerField(default=1)
    delivered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-delivered_at']
        verbose_name = 'Log de Webhook'
        verbose_name_plural = 'Logs de Webhooks'
        indexes = [
            models.Index(fields=['webhook', '-delivered_at']),
            models.Index(fields=['event_type', '-delivered_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.event_type} - {self.webhook.name}"


# ==============================================================================
# LOGS DE AUTENTICACIÓN (ya lo tienes, solo actualizar)
# ==============================================================================

class AuthLog(models.Model):
    """Registro de eventos de autenticación para auditoría."""
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='auth_logs'
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('login_failed', 'Login Failed'),
            ('register', 'Register'),
            ('password_reset', 'Password Reset'),
            ('password_change', 'Password Change'),
            ('email_verify', 'Email Verify'),
            ('token_refresh', 'Token Refresh'),
            ('2fa_verify', '2FA Verify'),
            ('2fa_failed', '2FA Failed'),
        ]
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Autenticación'
        verbose_name_plural = 'Logs de Autenticación'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'Anónimo'
        return f"{self.event_type} - {user_email} - {self.timestamp}"