# referral_project/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Базовый каталог
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных окружения из .env файла
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Секретный ключ
SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Отладка
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = []

# Приложения
INSTALLED_APPS = [
    # Стандартные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Внешние приложения
    'rest_framework',
    'drf_yasg',
    'corsheaders',  # Если используете CORS

    # Ваши приложения
    'accounts',
]

# Пользовательская модель
AUTH_USER_MODEL = 'accounts.User'

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Если используете CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL конфигурация
ROOT_URLCONF = 'referral_project.urls'

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Убедитесь, что директория 'templates' существует
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

# WSGI приложение
WSGI_APPLICATION = 'referral_project.wsgi.application'

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'referral_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Пароли
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # Добавьте другие валидаторы по необходимости
]

# Международные настройки
LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Статические файлы
STATIC_URL = '/static/'

# Caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Настройки REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Измените на INFO или WARNING в продакшене
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Настройки CORS
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

# Celery настройки
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# SMSAERO настройки
SMSAERO_EMAIL = os.getenv('SMSAERO_EMAIL')
SMSAERO_API_KEY = os.getenv('SMSAERO_API_KEY')
