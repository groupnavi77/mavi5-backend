"""
Schemas para funcionalidades avanzadas.
Crear como: core/user/api/schemas_advanced.py
"""

from ninja import Schema
from typing import Optional, List
from datetime import datetime


# ==============================================================================
# SCHEMAS DE ROLES Y PERMISOS
# ==============================================================================

class PermissionSchema(Schema):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    module: str


class RoleSchema(Schema):
    id: int
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: List[PermissionSchema]
    created_at: datetime


class RoleCreateSchema(Schema):
    name: str
    description: Optional[str] = None
    permission_codes: List[str] = []


class AssignRoleSchema(Schema):
    user_id: int
    role_name: str


# ==============================================================================
# SCHEMAS DE 2FA
# ==============================================================================

class TwoFactorEnableResponseSchema(Schema):
    success: bool
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    backup_codes: Optional[List[str]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class TwoFactorVerifySchema(Schema):
    code: str


class TwoFactorStatusSchema(Schema):
    enabled: bool
    last_used: Optional[datetime] = None


class LoginWith2FASchema(Schema):
    email: str
    password: str
    code: str


# ==============================================================================
# SCHEMAS DE WEBHOOKS
# ==============================================================================

class WebhookSchema(Schema):
    id: int
    name: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime


class WebhookCreateSchema(Schema):
    name: str
    url: str
    events: List[str]
    headers: Optional[dict] = {}


class WebhookLogSchema(Schema):
    id: int
    event_type: str
    response_status: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    attempts: int
    delivered_at: datetime


# ==============================================================================
# SCHEMAS DE ADMINISTRACIÓN
# ==============================================================================

class UserDetailAdminSchema(Schema):
    """Schema completo para administración."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    is_verified: bool
    provider: str
    roles: List[str]
    permissions: List[str]
    has_2fa: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class AuthLogSchema(Schema):
    """Schema para logs de autenticación."""
    id: int
    user_email: Optional[str] = None
    event_type: str
    ip_address: str
    success: bool
    details: Optional[str] = None
    timestamp: datetime


class DashboardStatsSchema(Schema):
    """Estadísticas del dashboard."""
    total_users: int
    verified_users: int
    active_users_today: int
    failed_logins_today: int
    users_with_2fa: int
    new_users_this_week: int


class UserActivitySchema(Schema):
    """Actividad de un usuario."""
    user_id: int
    user_email: str
    total_logins: int
    last_login: Optional[datetime] = None
    failed_attempts: int
    has_2fa: bool
    recent_activity: List[AuthLogSchema]