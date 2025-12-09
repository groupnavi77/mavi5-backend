from ninja import Schema
from pydantic import EmailStr
from typing import Optional

# --- Auth Schemas ---

class LoginSchema(Schema):
    email: str
    password: str

class UserCreateSchema(Schema):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class SocialAuthSchema(Schema):
    provider: str  # 'google', 'facebook', 'github'
    access_token: str
    id_token: Optional[str] = None  # Requerido para Google

class RefreshTokenSchema(Schema):
    refresh: str

class LogoutSchema(Schema):
    access: str
    refresh: str

# --- User & Response Schemas ---

class UserSchema(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    is_verified: bool

class TokenResponseSchema(Schema):
    success: bool
    message: Optional[str] = None
    refresh: Optional[str] = None
    access: Optional[str] = None
    user: Optional[UserSchema] = None
    error: Optional[str] = None

# --- User Update Schemas ---

class UserUpdateSchema(Schema):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PasswordChangeSchema(Schema):
    old_password: str
    new_password: str

class EmailRequestSchema(Schema):
    """Para solicitar el email (sirve para verificar y resetear)."""
    email: EmailStr

class EmailVerifyConfirmSchema(Schema):
    """Para confirmar la verificación del email."""
    token: str

class PasswordResetConfirmSchema(Schema):
    """Para establecer la nueva contraseña."""
    token: str
    new_password: str