import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

RUNNING_IN_DOCKER = os.getenv('IS_DOCKER', False) == 'DOCKER'

if not RUNNING_IN_DOCKER:
    load_dotenv('../infra/config/.general')
else:
    load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

env_debug = os.getenv('DEBUG', 'True').lower()
DEBUG = True if env_debug == 'true' else False

ALLOWED_HOSTS = [
    value.strip() for value in os.getenv('ALLOWED_HOSTS', '*').split(',')
]
CSRF_TRUSTED_ORIGINS = [
    value.strip()
    for value in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1').split(
        ','
    )
]
if DEBUG:
    ALLOWED_HOSTS.append('localhost')
    ALLOWED_HOSTS.append('127.0.0.1')
    CSRF_TRUSTED_ORIGINS.append('http://localhost')
    CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1')

INSTALLED_APPS = [
    'azucafe.apps.AzucafeConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'admin_panel.urls'

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
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

WSGI_APPLICATION = 'admin_panel.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('ENGINE'),
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST')
        if RUNNING_IN_DOCKER
        else 'localhost',
        'PORT': os.getenv('POSTGRES_PORT'),
    }
}

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

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'asserts',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_REDIRECT_URL = 'azucafe:cafe_list'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_FAILURE_VIEW = 'azucafe.views_error.csrf_error'
