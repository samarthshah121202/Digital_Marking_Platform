"""
Django settings for finalyearproject project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from finalyearproject.logging import LOGGING
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING_CONFIG = None
def create_assignments_folder_once():
    from django.conf import settings
    assignments_path = os.path.join(settings.BASE_DIR, 'assignments')
    if not os.path.exists(assignments_path):
        os.makedirs(assignments_path)

create_assignments_folder_once()
import logging.config
logging.config.dictConfig(LOGGING)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-x6f9=20c^+6_&7k*u(ohfrkj@u2#z495+g53&^94$s+g1gj$2w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["digital-marking-platform-ss-f11878c25b08.herokuapp.com", '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'finalyearproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'finalyearproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
import dj_database_url
import os

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',  # fallback for local dev
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# grading_platform/settings.py


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'  # URL to use when referring to static files

# Optional settings for local development
STATICFILES_DIRS = [
    # BASE_DIR / "student_works",  # Ensure this path is correct  
    BASE_DIR / "assignments",  # Ensure this path is correct  
    BASE_DIR / "static"
]

# Path to collect static files for deployment (usually ignored during local development)
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/'

# Media files configuration
from loginsights.main import LogInsightsLogger

# Configuration variables (replace with your own details)
connection_string = "https://insightsfyp.queue.core.windows.net/messages?sv=2024-11-04&se=2026-02-02T17%3A19%3A39Z&sp=a&sig=HLdYQTb1R7jfV8J79t3qG%2FrSWOaZ0CQK0p46xk0ima4%3D"  # Replace with your connection string
client_application_id = 7  # Replace with the given client application id
secret = "X2oDWpC701b5bG2YxU1BujKdXB7BdsvSGKFEzJh52oHEl7sjzJN2r4kyrLpUsBdHFJyRByjox5JFbG2aTXMUe3kMjQWoeMM1L98bIbhAjjEvvfXkSOBUzInLimsub5Kk"  # Replace with the given secret

config = {
    "ConnectionString": connection_string,
    "ClientApplicationId": client_application_id,
    "Secret": secret
}

# Configure the logger
LogInsightsLogger.configure(config)

