import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=None):
    val = os.environ.get(key)
    if not val:
        return default or []
    return [x.strip() for x in val.split(',') if x.strip()]


SECRET_KEY = env('SECRET_KEY', 'youthguard-secret-key-change-in-production-2024')
DEBUG = env_bool('DEBUG', True)

# Domen va hostlar
DOMAIN = env('DOMAIN', 'sam-auth.uz')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', ['*'])

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8001',
    'https://sam-auth.uz',
    'https://www.sam-auth.uz',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
])

# Reverse-proxy (nginx) orqasida HTTPS ni to'g'ri aniqlash
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'apps.accounts',
    'apps.youth',
    'apps.meetings',
    'apps.surveys',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database: agar POSTGRES_DB env bo'lsa Postgres, aks holda lokal SQLite
if env('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', 'youthguard'),
            'USER': env('POSTGRES_USER', 'postgres'),
            'PASSWORD': env('POSTGRES_PASSWORD', 'postgres'),
            'HOST': env('POSTGRES_HOST', 'db'),
            'PORT': env('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

BOT_SECRET_KEY = env('BOT_SECRET_KEY', 'youthguard-bot-secret-2024')
BOT_TOKEN = env('BOT_TOKEN', '8595307417:AAG1Zv_hmfNm31oL5vvB4ke_xLS5oD2uEEk')
# Bot xabarlardagi web linklar uchun tashqi manzil (ngrok yoki domen)
PUBLIC_URL = env('PUBLIC_URL', 'https://sam-auth.uz')
NGROK_URL = env('NGROK_URL', PUBLIC_URL)

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

JAZZMIN_SETTINGS = {
    "site_title": "YouthGuard Admin",
    "site_header": "YouthGuard",
    "site_brand": "YouthGuard",
    "welcome_sign": "YouthGuard tizimiga xush kelibsiz",
    "copyright": "YouthGuard 2024",
    "search_model": ["accounts.CustomUser", "youth.Youth", "meetings.Meeting"],
    "topmenu_links": [
        {"name": "Bosh sahifa", "url": "/", "new_window": False},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "accounts.customuser": "fas fa-users",
        "accounts.district": "fas fa-map",
        "accounts.organization": "fas fa-building",
        "youth.youth": "fas fa-child",
        "meetings.meeting": "fas fa-handshake",
        "meetings.verification": "fas fa-check-circle",
        "meetings.actionlog": "fas fa-history",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-success",
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-white navbar-light",
    "theme": "default",
}
