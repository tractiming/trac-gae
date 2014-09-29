"""
Django settings for trac-gae project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os

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
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'updates',
    'users',
    'results',
    'common',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
# Here we choose the backend based on whether we are running locally or in
# production. For reference, see:
# https://developers.google.com/appengine/docs/python/cloud-sql/django#development-settings
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'HOST': '/cloudsql/trac-us:sql1',
                'NAME': 'tracdb',
                'USER': 'root',
            }
    }
elif os.getenv('SETTINGS_MODE') == 'prod':
    # Running in development, but want to access the Google Cloud SQL instance
    # in production.
    DATABASES = {
            'default': {
                'ENGINE': 'google.appengine.ext.django.backends.rdbms',
                'INSTANCE': 'trac-us:sql1',
                'NAME': 'tracdb',
                'USER': 'root',
            }
    }
else:
    # Running in development, so use a local MySQL database.
    # Note: not implemented yet.
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(PROJECT_PATH, 'dev_loc.db'),
                #'NAME': 'tracdb',
                #'USER': 'root',
                #'PASSWORD': 'password',
            }
    }

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

