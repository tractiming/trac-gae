"""
Django settings for tracd project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from djangoappengine.settings_base import *

import os

# Activate django-dbindexer for the default database.
DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
AUTOLOAD_SITECONF = 'indexes'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
SETTINGS_DIR = os.path.dirname(__file__)
PROJECT_PATH = os.path.abspath(SETTINGS_DIR)
TEMPLATE_PATH = os.path.join(PROJECT_PATH, 'templates')
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gi8u=tes8q2*@@1lkfu69j^1&syc+p)l0%i0ut4$a3@5c&9b4z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'updates',
    #'users',
    #'results',
    'common',
    'djangotoolbox',
    'autoload',
    'dbindexer',
    'djangoappengine', # This should come last.
)

MIDDLEWARE_CLASSES = (
    'autoload.middleware.AutoloadMiddleware', # This should come first.    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'trac',
#        'HOST': 'localhost',
#        'USER': 'elliot',
#        'PASSWORD': 'millie',
#    }
#}

#CACHES = {
#        'default': {
#            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#            'LOCATION': '127.0.0.1:11211',
#        }
#}

TEMPLATE_DIRS = (
        TEMPLATE_PATH,
)


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = (
        os.path.join(SETTINGS_DIR, "static"),
)
