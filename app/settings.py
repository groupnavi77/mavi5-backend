"""
Django settings for full_auth project.
Optimized for Django Ninja + PyJWT (No DRF).
"""

import sys
import os
from os import getenv, path
from pathlib import Path
from datetime import timedelta # ⬅️ Importante para los tokens
import dotenv
import dj_database_url
import pymysql

# Configuración de driver MySQL
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno
dotenv_file = BASE_DIR / '.env.local'
if path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

DEVELOPMENT_MODE = getenv('DEVELOPMENT_MODE', 'False') == 'True'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv('DJANGO_SECRET_KEY', 'django-insecure-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

CSRF_TRUSTED_ORIGINS = ['https://api.avisosya.pe']

# Configuración CORS
CORS_ALLOWED_ORIGINS = getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,https://avisosya.pe,https://www.avisosya.pe'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# =========================================================
# 📦 APLICACIONES INSTALADAS (LIMPIO)
# =========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Utilidades
    'corsheaders',
    'django_filters', # Mantenido por si usas filtros en Ninja
    'storages',       # Para AWS S3
    'anymail',        # Para Brevo
    'mptt',
    'ninja_extra',           # Para categorías jerárquicas
    
    # Manejo de Imágenes y Texto
    'taggit',
    'taggit_serializer', # Puedes evaluar si esto sigue siendo necesario sin DRF
    'tinymce',
    'easy_thumbnails',
    
    # Tus Aplicaciones
    'core.product_base',
    'core.user',
    'core.category',
    'core.product_ins',
    'core.tag',
    'core.review',
    'core.campaing',
]

# =========================================================
# 🛡️ MIDDLEWARE (LIMPIO)
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS debe ir alto
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Eliminado: SocialAuthExceptionMiddleware
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Eliminados context processors de social_django
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# =========================================================
# 🗄️ BASE DE DATOS
# =========================================================
if DEVELOPMENT_MODE is True:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif len(sys.argv) > 0 and sys.argv[1] != 'collectstatic':
    if getenv('DATABASE_URL', None) is None:
        raise Exception('DATABASE_URL environment variable not defined')
    DATABASES = {
        'default': dj_database_url.parse(getenv('DATABASE_URL')),
    }

# =========================================================
# 👤 USUARIO Y AUTENTICACIÓN
# =========================================================
AUTH_USER_MODEL = 'user.UserAccount'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Eliminados los backends de social_core (Google, Facebook, etc)
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# =========================================================
# 🔑 CONFIGURACIÓN JWT (CUSTOM / NINJA)
# =========================================================
# Estas variables son leídas por tu UserService para generar tokens con PyJWT
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)  # Ajusta según necesidad
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

# =========================================================
# 📧 EMAIL SETTINGS
# =========================================================
ADMINS = [("Administrador", "groupnavi77@gmail.com")]

if DEVELOPMENT_MODE is True:  
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_SUBJECT_PREFIX = "AvisoYa.pe "  
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    DEFAULT_FROM_EMAIL = "Avisosya.pe <secure@avisosya.pe>"
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    ANYMAIL = {
        "BREVO_API_KEY": getenv("BREVO_API_KEY"),
    }

# =========================================================
# 🌍 INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Lima' # Recomendado usar UTC en BD y convertir en frontend
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =========================================================
# ☁️ STATIC & MEDIA FILES (AWS S3)
# =========================================================
DOMAIN = getenv('DOMAIN')
SITE_NAME = 'Avisosya.pe'

if DEVELOPMENT_MODE is True:
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'static'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    # AWS S3 Configuration
    AWS_S3_REGION_NAME = 'us-east-2'
    AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    AWS_QUERYSTRING_EXPIRE = 3600
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read'

    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

    # Storages (Django 4.2+)
    STORAGES = {
        "default": {"BACKEND": "custom_storages.MediaStorage"},
        "staticfiles": {"BACKEND": "custom_storages.StaticStorage"}
    }
    
    # Configuración para Easy Thumbnails en S3
    THUMBNAIL_DEFAULT_STORAGE = 'custom_storages.MediaStorage'

STATICFILES_DIRS = [ BASE_DIR / 'app/statics' ]

# settings.py

STATICFILES_FINDERS = [
    # 1. Busca archivos en las carpetas listadas en STATICFILES_DIRS
    'django.contrib.staticfiles.finders.FileSystemFinder',
    
    # 🌟 2. ¡CRÍTICO! Busca archivos dentro de las apps instaladas (incluyendo Admin)
    'django.contrib.staticfiles.finders.AppDirectoriesFinder', 
]

# =========================================================
# 🖼️ EASY THUMBNAILS
# =========================================================
AWS_QUERYSTRING_AUTH = False
THUMBNAIL_ALIASES = {
    '': {
        'img800': {'size': (900, 900), 'crop': True},
        'img316': {'size': (300, 300), 'crop': True},
        'img270': {'size': (270, 270), 'crop': True},
    },
}
THUMBNAIL_EXTENSION = 'jpg'
THUMBNAIL_NAMER = 'easy_thumbnails.namers.source_hashed'

# Estas rutas locales se ignoran si usas S3 en producción, 
# pero son útiles para desarrollo.
THUMBNAIL_MEDIA_ROOT = BASE_DIR / 'media/thumbnails'
THUMBNAIL_MEDIA_URL = '/media/thumbnails/'

# =========================================================
# 🚀 CACHÉ Y OTROS
# =========================================================
# ==============================================================================
# CONFIGURACIÓN DE CACHÉ CON MYSQL
# ==============================================================================

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tag handling
TAGGIT_TAGS_FROM_STRING = 'core.product_base.utils.clean_tag_string_and_split'

# Login/Logout URLs (Opcionales si la API es 100% headless, pero bueno tenerlos)
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/'