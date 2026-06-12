from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tutlee-dev-key-replace-in-production-2026')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    # Local apps
    'accounts',
    'sessions_app',
    'assessments',
    'kyt',
    'study_rings',
    'reports',
    'payments',
]

MIDDLEWARE = [
    'tutlee.middleware.ForceCORSMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tutlee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent],   # serves index.html, admin.html from parent folder
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

WSGI_APPLICATION = 'tutlee.wsgi.application'
ASGI_APPLICATION = 'tutlee.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
WHITENOISE_USE_FINDERS = True
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST FRAMEWORK ──
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# ── JWT ──
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS':  True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── CORS ──
CORS_ALLOW_ALL_ORIGINS   = True
CORS_ORIGIN_ALLOW_ALL    = True   # legacy alias for older django-cors-headers
CORS_ALLOW_CREDENTIALS   = True
CORS_PREFLIGHT_MAX_AGE   = 86400
CORS_ALLOW_HEADERS       = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]
CORS_ALLOW_METHODS = ['DELETE','GET','OPTIONS','PATCH','POST','PUT']
# ── EMAIL ──
# Auto-switches to SMTP when EMAIL_HOST_USER + EMAIL_HOST_PASSWORD env vars are set.
# On Render: add those two vars in the Environment tab to enable real email sending.
# Without them the backend logs OTP to console and returns dev_otp_code in the
# register API response so the frontend can auto-fill the field during testing.
import os as _os
EMAIL_HOST          = _os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(_os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = _os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = _os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = _os.environ.get('EMAIL_HOST_PASSWORD', '')
# Gmail requires FROM to match the authenticated account — fall back to that
_default_from = f'Tutlee <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'Tutlee <noreply@tutlee.com>'
DEFAULT_FROM_EMAIL  = _os.environ.get('DEFAULT_FROM_EMAIL', _default_from)

# Use real SMTP when credentials are present, console otherwise
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = _os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
else:
    EMAIL_BACKEND = _os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
