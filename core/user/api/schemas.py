# core/user/api/schemas.py - VERSIÓN COMPLETA

from ninja import Schema
from pydantic import EmailStr, field_validator
from typing import Optional

# ==============================================================================
# SCHEMAS DE AUTENTICACIÓN
# ==============================================================================

class LoginSchema(Schema):
    """Schema para login de usuario."""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        """Convierte el email a minúsculas."""
        return v.lower().strip()


class UserCreateSchema(Schema):
    """Schema para registro de usuario."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip().title()


class SocialAuthSchema(Schema):
    """Schema para autenticación social."""
    provider: str  # 'google', 'facebook', 'github'
    access_token: str
    id_token: Optional[str] = None  # Requerido solo para Google
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = ['google', 'facebook', 'github']
        if v.lower() not in allowed:
            raise ValueError(f'Provider debe ser uno de: {", ".join(allowed)}')
        return v.lower()


class RefreshTokenSchema(Schema):
    """Schema para refrescar token."""
    refresh: str


class LogoutSchema(Schema):
    """Schema para logout."""
    access: str
    refresh: str


# ==============================================================================
# SCHEMAS DE USUARIO
# ==============================================================================

class UserSchema(Schema):
    """Schema básico de usuario para respuestas."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    is_active: bool
    provider: str
    created_at: Optional[str] = None


class UserUpdateSchema(Schema):
    """Schema para actualizar información del usuario."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: Optional[str]) -> Optional[str]:
        return v.lower().strip() if v else None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def name_format(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().title() if v else None


# ==============================================================================
# SCHEMAS DE RESPUESTA
# ==============================================================================

class TokenResponseSchema(Schema):
    """Schema de respuesta para operaciones de auth."""
    success: bool
    message: Optional[str] = None
    refresh: Optional[str] = None
    access: Optional[str] = None
    user: Optional[UserSchema] = None
    error: Optional[str] = None


# ==============================================================================
# SCHEMAS DE CONTRASEÑA
# ==============================================================================

class PasswordChangeSchema(Schema):
    """Schema para cambio de contraseña (usuario autenticado)."""
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class PasswordResetConfirmSchema(Schema):
    """Schema para confirmar reset de contraseña."""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


# ==============================================================================
# SCHEMAS DE EMAIL
# ==============================================================================

class EmailRequestSchema(Schema):
    """Schema para solicitar email (verificación o reset)."""
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class EmailVerifyConfirmSchema(Schema):
    """Schema para confirmar verificación de email."""
    token: str


# ==============================================================================
# SCHEMAS DE PERFIL (OPCIONAL - Para futuro)
# ==============================================================================

class UserProfileSchema(Schema):
    """Schema extendido con información de perfil."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    is_active: bool
    is_staff: bool
    provider: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None


class UserProfileUpdateSchema(Schema):
    """Schema para actualizar perfil extendido."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    
    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError('La biografía no puede exceder 500 caracteres')
        return v.strip() if v else None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Remover espacios y caracteres no numéricos (excepto +)
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 8:
                raise ValueError('Número de teléfono inválido')
            return cleaned
        return None


# ==============================================================================
# SCHEMAS DE ERROR (OPCIONAL - Para respuestas consistentes)
# ==============================================================================

class ErrorSchema(Schema):
    """Schema estándar para errores."""
    success: bool = False
    error: str
    code: Optional[str] = None
    details: Optional[dict] = None


# ==============================================================================
# SCHEMAS DE ÉXITO (OPCIONAL)
# ==============================================================================

class SuccessSchema(Schema):
    """Schema estándar para respuestas exitosas."""
    success: bool = True
    message: str
    data: Optional[dict] = None