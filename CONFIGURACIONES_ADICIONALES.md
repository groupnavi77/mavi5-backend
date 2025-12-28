# CONFIGURACIONES_ADICIONALES.md

# ⚙️ Configuraciones Adicionales Recomendadas

## 📁 ESTRUCTURA DE ARCHIVOS A CREAR

```
core/user/
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── init_user_system.py        # ← Management command
├── templatetags/
│   ├── __init__.py
│   └── user_admin_extras.py          # ← Template tags
├── admin.py                            # ← Admin mejorado
└── ...

templates/
└── admin/
    └── user/
        ├── analytics.html              # ← Vista de analíticas
        └── activity.html               # ← Vista de actividad
```

---

## 🔧 PASOS DE INSTALACIÓN COMPLETOS

### 1. Crear directorios necesarios

```bash
# Desde la raíz del proyecto

# Crear directorio de management commands
mkdir -p core/user/management/commands
touch core/user/management/__init__.py
touch core/user/management/commands/__init__.py

# Crear directorio de templatetags
mkdir -p core/user/templatetags
touch core/user/templatetags/__init__.py

# Crear directorio de templates del admin
mkdir -p templates/admin/user
```

### 2. Copiar archivos

```bash
# Copiar admin.py
cp admin.py core/user/admin.py

# Copiar templates
cp admin_analytics.html templates/admin/user/analytics.html
cp admin_activity.html templates/admin/user/activity.html

# Copiar template tags
cp user_admin_extras.py core/user/templatetags/user_admin_extras.py

# Copiar management command
cp init_user_system.py core/user/management/commands/init_user_system.py
```

### 3. Verificar settings.py

```python
# settings.py

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ← Importante!
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Asegúrate de tener estas apps instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tus apps
    'core.user',
    # ...
]
```

### 4. Inicializar el sistema

```bash
# Hacer migraciones (si es necesario)
python manage.py makemigrations
python manage.py migrate

# Crear tabla de caché (para rate limiting)
python manage.py createcachetable

# Inicializar roles y permisos
python manage.py init_user_system

# Opcional: Crear usuarios de demo
python manage.py init_user_system --create-demo-users
```

---

## 🎨 PERSONALIZACIÓN DEL ADMIN

### Agregar logo personalizado en el admin

```python
# settings.py

ADMIN_SITE_HEADER = "Avisosya.pe Admin"
ADMIN_SITE_TITLE = "Avisosya Admin"
ADMIN_INDEX_TITLE = "Panel de Administración"
```

### Agregar en urls.py

```python
# app/urls.py
from django.contrib import admin

admin.site.site_header = "Avisosya.pe Admin"
admin.site.site_title = "Avisosya Admin"
admin.site.index_title = "Panel de Administración"
```

---

## 📊 CONFIGURAR CACHÉ PARA RATE LIMITING

### En settings.py:

```python
# Caché con base de datos (ya lo tienes configurado)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
        'TIMEOUT': 900,  # 15 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
            'CULL_FREQUENCY': 3,
        }
    }
}
```

### Crear tabla de caché:

```bash
python manage.py createcachetable
```

---

## 🔐 CONFIGURAR PERMISOS PERSONALIZADOS

### Ejemplo de uso en endpoints:

```python
# core/user/api/endpoints.py
from .permissions import require_permissions

@router.get('/admin/users', auth=jwt_auth)
@require_permissions(authenticated=True, staff=True)
def list_users(request):
    """Solo accesible para staff."""
    users = UserAccount.objects.all()
    return {"users": [...]}

@router.post('/products', auth=jwt_auth)
@require_permissions(authenticated=True, verified=True)
def create_product(request, payload):
    """Requiere email verificado."""
    # Crear producto
    pass
```

### Ejemplo con roles:

```python
from .permissions import has_role

@router.post('/products/approve', auth=jwt_auth)
@has_role('Admin', 'Moderator')
def approve_product(request, product_id: int):
    """Solo Admin y Moderator pueden aprobar."""
    # Aprobar producto
    pass
```

---

## 📧 CONFIGURAR TEMPLATES DE EMAIL

### Crear templates adicionales:

```bash
mkdir -p templates/email
```

### Ejemplo de template de bienvenida:

```html
<!-- templates/email/welcome_email.txt -->
Hola {{ user.first_name }},

¡Bienvenido a Avisosya.pe! 🎉

Tu cuenta ha sido creada exitosamente. Ahora puedes:
- Crear y gestionar tus productos
- Participar en campañas
- Gestionar tu perfil

Si tienes alguna pregunta, no dudes en contactarnos.

Saludos,
El equipo de Avisosya.pe
```

---

## 🔍 LOGGING Y DEBUGGING

### Configurar logging en settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/auth.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'core.user': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Crear directorio de logs:

```bash
mkdir logs
touch logs/.gitkeep
```

### Agregar a .gitignore:

```
logs/*.log
```

---

## 🧪 TESTING

### Crear tests para el admin:

```python
# core/user/tests/test_admin.py

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.user.models import Role, Permission

User = get_user_model()

class AdminTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='Test'
        )
        self.client.login(email='admin@test.com', password='testpass123')
    
    def test_admin_accessible(self):
        """Test que el admin sea accesible."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_list_view(self):
        """Test que la lista de usuarios funcione."""
        response = self.client.get('/admin/user/useraccount/')
        self.assertEqual(response.status_code, 200)
    
    def test_analytics_view(self):
        """Test que la vista de analíticas funcione."""
        response = self.client.get('/admin/user/useraccount/analytics/')
        self.assertEqual(response.status_code, 200)
```

---

## 🔄 TAREAS PROGRAMADAS (OPCIONAL)

### Usando Django Q o Celery para limpiar logs automáticamente:

```python
# core/user/tasks.py

from django.utils import timezone
from datetime import timedelta
from .models import AuthLog, TokenBlacklist, WebhookLog

def cleanup_old_logs():
    """Limpia logs antiguos."""
    # Eliminar logs de auth mayores a 90 días
    ninety_days_ago = timezone.now() - timedelta(days=90)
    AuthLog.objects.filter(timestamp__lt=ninety_days_ago).delete()
    
    # Eliminar tokens expirados
    TokenBlacklist.objects.filter(expires_at__lt=timezone.now()).delete()
    
    # Eliminar webhook logs mayores a 30 días
    thirty_days_ago = timezone.now() - timedelta(days=30)
    WebhookLog.objects.filter(delivered_at__lt=thirty_days_ago).delete()
```

---

## 🛡️ SEGURIDAD ADICIONAL

### Configurar CORS correctamente:

```python
# settings.py

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://avisosya.pe",
    "https://www.avisosya.pe",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
```

### Configurar rate limiting a nivel de servidor (Nginx):

```nginx
# nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

---

## 📱 NOTIFICACIONES (OPCIONAL)

### Configurar notificaciones por email para eventos importantes:

```python
# core/user/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import AuthLog

@receiver(post_save, sender=AuthLog)
def notify_failed_logins(sender, instance, created, **kwargs):
    """Notifica cuando hay muchos intentos fallidos."""
    if created and instance.event_type == 'login_failed':
        # Contar intentos fallidos recientes
        recent_failures = AuthLog.objects.filter(
            user=instance.user,
            event_type='login_failed',
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures >= 5:
            send_mail(
                'Alerta: Múltiples intentos de login fallidos',
                f'Se detectaron {recent_failures} intentos fallidos para {instance.user.email}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMINS[0][1]],
                fail_silently=True,
            )
```

---

## 📈 MÉTRICAS Y MONITOREO

### Agregar métricas personalizadas:

```python
# core/user/metrics.py

from django.utils import timezone
from datetime import timedelta
from .models import UserAccount, AuthLog

def get_system_metrics():
    """Obtiene métricas del sistema."""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    return {
        'total_users': UserAccount.objects.count(),
        'active_users_24h': AuthLog.objects.filter(
            event_type='login',
            success=True,
            timestamp__gte=last_24h
        ).values('user').distinct().count(),
        'new_users_7d': UserAccount.objects.filter(
            created_at__gte=last_7d
        ).count(),
        'failed_logins_24h': AuthLog.objects.filter(
            event_type='login_failed',
            timestamp__gte=last_24h
        ).count(),
    }
```

---

## 🎯 COMANDOS ÚTILES

### Crear superusuario:
```bash
python manage.py createsuperuser
```

### Inicializar sistema:
```bash
python manage.py init_user_system --create-demo-users
```

### Limpiar tokens expirados:
```bash
python manage.py shell
>>> from core.user.models import TokenBlacklist
>>> from django.utils import timezone
>>> TokenBlacklist.objects.filter(expires_at__lt=timezone.now()).delete()
```

### Ver estadísticas rápidas:
```bash
python manage.py shell
>>> from core.user.metrics import get_system_metrics
>>> print(get_system_metrics())
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

### Agregar documentación del API:

```python
# app/api.py
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="Mavi API",
    version="1.0.0",
    description="""
    API completa para Mavi Store.
    
    ## Autenticación
    Usa JWT tokens en el header: `Authorization: Bearer <token>`
    
    ## Rate Limiting
    - Login: 5 intentos cada 5 minutos
    - Registro: 3 intentos por hora
    - Refresh Token: 10 intentos por minuto
    
    ## Roles Disponibles
    - Admin: Acceso completo
    - Moderator: Gestión de contenido
    - Designer: Creación de productos
    - Support: Atención al cliente
    - Customer: Usuario básico
    """,
    docs_url="/api/docs",  # Swagger UI
    openapi_url="/api/openapi.json"
)
```

---

## ✅ CHECKLIST FINAL

- [ ] Directorios creados
- [ ] Archivos copiados
- [ ] Settings.py configurado
- [ ] Migraciones ejecutadas
- [ ] Tabla de caché creada
- [ ] Sistema inicializado
- [ ] Usuarios demo creados (opcional)
- [ ] Templates funcionando
- [ ] Admin accesible
- [ ] Exportaciones probadas
- [ ] Vistas personalizadas funcionando
- [ ] Rate limiting probado
- [ ] Emails configurados
- [ ] Logs funcionando
- [ ] Tests creados (opcional)

---

## 🆘 TROUBLESHOOTING

### Error: TemplateDoesNotExist
**Solución:** Verifica que `DIRS` en `TEMPLATES` apunte correctamente a la carpeta templates.

### Error: No module named 'core.user.templatetags'
**Solución:** Asegúrate de que existe el archivo `__init__.py` en `core/user/templatetags/`.

### Error: Table 'cache_table' doesn't exist
**Solución:** Ejecuta `python manage.py createcachetable`.

### Error al exportar CSV
**Solución:** El BOM está incluido. Verifica que tu navegador no está bloqueando descargas.

### Admin muy lento
**Solución:** Agrega `select_related()` y `prefetch_related()` en queries pesadas.

---

¡Todo listo para producción! 🚀
