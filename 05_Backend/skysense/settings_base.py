"""
SKYsense AI - Base Django Settings
Shared settings inherited by development and production configurations.
"""

import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"

# Load environment variables from .env files (root or backend)
def _load_env_file(env_file: Path):
    if env_file.is_file():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

_load_env_file(REPO_ROOT / ".env")
_load_env_file(BASE_DIR / ".env")

# Ensure 03_AI_Model is on sys.path for direct AI inference integration
for path_item in [str(BASE_DIR), str(AI_MODEL_DIR)]:
    if path_item not in sys.path:
        sys.path.insert(0, path_item)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # SkySense AI Apps
    'core.apps.CoreConfig',
    'predictions.apps.PredictionsConfig',
    'accounts.apps.AccountsConfig',
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

ROOT_URLCONF = 'skysense.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.system_status',
            ],
        },
    },
]

WSGI_APPLICATION = 'skysense.wsgi.application'
ASGI_APPLICATION = 'skysense.asgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploaded images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Upload Constraints & Security Limits
max_mb_env = os.environ.get('MAX_UPLOAD_SIZE_MB', '15')
try:
    MAX_UPLOAD_SIZE_MB = int(max_mb_env)
except ValueError:
    MAX_UPLOAD_SIZE_MB = 15

MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # default: 15 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

ALLOWED_IMAGE_EXTENSIONS = [
    ext.strip().lower() for ext in
    os.environ.get('ALLOWED_IMAGE_EXTENSIONS', '.jpg,.jpeg,.png').split(',')
    if ext.strip()
]
ALLOWED_IMAGE_MIME_TYPES = [
    mime.strip().lower() for mime in
    os.environ.get('ALLOWED_IMAGE_MIME_TYPES', 'image/jpeg,image/png').split(',')
    if mime.strip()
]

# Defensive Baseline HTTP Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# AI Model Configuration Reference
AI_BEST_MODEL_PATH = AI_MODEL_DIR / "models" / "best_xception_rainfall.keras"
AI_TFLITE_MODEL_PATH = AI_MODEL_DIR / "models" / "xception_rainfall.tflite"

# Authentication Configuration
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
