from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# === Toggles de entorno
USE_PROD = config('USE_PROD', cast=bool, default=False)
USE_S3   = config('USE_S3',   cast=bool, default=False)

SECRET_KEY = config('SECRET_KEY', default='change-me')
DEBUG = config('DEBUG', cast=bool, default=not USE_PROD)
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')]

LANGUAGE_CODE = config('LANGUAGE_CODE', default='es')
TIME_ZONE = config('TIME_ZONE', default='America/Argentina/Buenos_Aires')
USE_I18N = True
USE_TZ = True

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'storages',
    'accounts',
    'propiedades',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_inmobiliaria.urls'
WSGI_APPLICATION = 'django_inmobiliaria.wsgi.application'

# === Templates (creamos luego; por ahora placeholders en views)
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
        BASE_DIR / 'templates',                           # si algún día usás esta ruta
        BASE_DIR / 'django_inmobiliaria' / 'templates',   # ← tu carpeta actual
    ],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]


# === BD: SQLite en dev | Postgres en prod
if USE_PROD:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     config('DB_NAME'),
            'USER':     config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST':     config('DB_HOST'),
            'PORT':     config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# === Archivos estáticos y media
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [BASE_DIR / "static"]


MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# STORAGES por entorno
if USE_PROD and USE_S3:
    from .storages import MediaStorage, StaticStorage
    STORAGES = {
        "default":     {"BACKEND": "django_inmobiliaria.storages.MediaStorage"},
        "staticfiles": {"BACKEND": "django_inmobiliaria.storages.StaticStorage"},
    }
    AWS_S3_REGION_NAME       = config('AWS_S3_REGION_NAME', default='sa-east-1')
    AWS_MEDIA_BUCKET         = config('AWS_MEDIA_BUCKET', default=config('AWS_STORAGE_BUCKET_NAME', default=None))
    AWS_STATIC_BUCKET        = config('AWS_STATIC_BUCKET', default=None)
    AWS_MEDIA_CUSTOM_DOMAIN  = config('AWS_MEDIA_CUSTOM_DOMAIN', default=None)
    AWS_STATIC_CUSTOM_DOMAIN = config('AWS_STATIC_CUSTOM_DOMAIN', default=None)
else:
    STORAGES = {
        "default":     {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# === Auth: usuario custom (DNI)
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"

# === Sesión: autologout 10 min (sliding)
SESSION_COOKIE_AGE = 600
SESSION_SAVE_EVERY_REQUEST = True

# === Cache (simple; luego Redis si querés)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "inmo-cache",
        "TIMEOUT": 300,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad recomendada en prod (HTTPS)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = USE_PROD
CSRF_COOKIE_SECURE = USE_PROD
