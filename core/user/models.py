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


class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
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