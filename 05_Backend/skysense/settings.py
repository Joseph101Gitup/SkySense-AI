"""
Django settings for SkySenseWeb project.
Inherits from settings_base.py and applies environment-aware configuration.
Dedicated production settings reside in skysense.settings_prod.
"""

import os
import sys
import urllib.parse
from pathlib import Path
from .settings_base import *

# Check execution context
IS_TESTING = 'test' in sys.argv
IS_DEPLOY_CHECK = '--deploy' in sys.argv
IS_PROD_ENV = os.environ.get('DJANGO_ENV', '').strip().lower() in ('prod', 'production')

# Debug mode: False if checking deployment or explicitly configured False
if IS_DEPLOY_CHECK or IS_PROD_ENV:
    DEBUG = False
elif IS_TESTING:
    DEBUG = False
else:
    DEBUG = os.environ.get('DJANGO_DEBUG', 'True').strip().lower() in ('true', '1', 'yes')

# Secret key resolution from environment variable
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'skysense-ai-secure-master-thesis-project-key-2026-fallback-dev'
)

# Allowed hosts resolution: never empty in production
allowed_hosts_raw = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if allowed_hosts_raw:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '[::1]']
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'skysense.ai', '.skysense.ai']

# CSRF Trusted Origins
csrf_trusted_raw = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if csrf_trusted_raw:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_trusted_raw.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'https://skysense.ai',
        'https://*.skysense.ai',
    ]

# SSL & Security Cookie Controls
if IS_TESTING:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
elif IS_DEPLOY_CHECK or IS_PROD_ENV:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    WHITENOISE_MANIFEST_STRICT = False
elif not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'True').strip().lower() in ('true', '1')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    WHITENOISE_MANIFEST_STRICT = False
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    WHITENOISE_MANIFEST_STRICT = False

# Database Configuration (Development & Production Routing)
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
DB_ENGINE = os.environ.get('DB_ENGINE', '').strip()

if DATABASE_URL:
    parsed = urllib.parse.urlparse(DATABASE_URL)
    if parsed.scheme in ('postgres', 'postgresql'):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed.path.lstrip('/'),
                'USER': urllib.parse.unquote(parsed.username or ''),
                'PASSWORD': urllib.parse.unquote(parsed.password or ''),
                'HOST': parsed.hostname or 'localhost',
                'PORT': parsed.port or 5432,
                'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
            }
        }
    elif parsed.scheme == 'sqlite':
        sqlite_path = parsed.path
        if sqlite_path.startswith('/') and len(sqlite_path) > 2 and sqlite_path[2] == ':':
            sqlite_path = sqlite_path[1:]
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Path(sqlite_path) if sqlite_path else (BASE_DIR / 'db.sqlite3'),
                'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
            }
        }
elif DB_ENGINE and DB_ENGINE != 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ.get('DB_NAME', 'skysense_db'),
            'USER': os.environ.get('DB_USER', 'skysense_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')) if not DEBUG else 0,
        }
    }
