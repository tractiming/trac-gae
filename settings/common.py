"""
Django settings for trac-gae project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from os.path import abspath, basename, dirname, join, normpath
from os import getenv
from sys import path

########## PATH CONFIGURATION ##########
DJANGO_ROOT = dirname(dirname(abspath(__file__)))
SITE_ROOT = dirname(DJANGO_ROOT)
SITE_NAME = basename(DJANGO_ROOT)
path.append(DJANGO_ROOT)

# Add the location of third-party libraries to the path.
path.insert(0, join(DJANGO_ROOT, 'libs'))

# Add the location of the apps to the path.
path.insert(0, join(DJANGO_ROOT, 'apps'))
########################################

########## SECRET CONFIGURATION ##########
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gi8u=tes8q2*@@1lkfu69j^1&syc+p)l0%i0ut4$a3@5c&9b4z'
ALLOWED_HOSTS = []
##########################################

########## DEBUG CONFIGURATION ##########
DEBUG = False
TEMPLATE_DEBUG = DEBUG
#########################################

########## MANAGER CONFIGURATION ##########
ADMINS = (
    ('elliot', 'ejhevel@gmail.com'),
)
MANAGERS = ADMINS
###########################################

########## APP CONFIGURATION ##########
DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

THIRD_PARTY_APPS = (
        'rest_framework',
        'provider',
        'provider.oauth2',
        'south',
)

LOCAL_APPS = (
        'trac',
        'api',
        'website',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
########################################

########## MIDDLEWARE CONFIGURATION ##########
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

##############################################
REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
        ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.OAuth2Authentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.BasicAuthentication',
        ),
        'DEFAULT_MODEL_SERIALIZER_CLASS': (
            'rest_framework.serializers.ModelSerializer',
        ),
}

################ SOUTH ################
SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True
#######################################

########## URL CONFIGURATION ##########
ROOT_URLCONF = 'trac.urls'
#######################################

########## DATABASE CONFIGURATION ##########
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
# Here we choose the backend based on whether we are running locally or in
# production. For reference, see:
# https://developers.google.com/appengine/docs/python/cloud-sql/django#development-settings
if getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'HOST': '/cloudsql/trac-us:sql1',
                'NAME': 'tracdb',
                'USER': 'root',
            }
    }

elif getenv('SETTINGS_MODE') == 'prod':
    # Running in development, but want to access the Google Cloud SQL instance
    # in production.
    SOUTH_DATABASE_ADAPTERS = {'default': 'south.db.mysql'}
    DATABASES = {
            'default': {
                'ENGINE': 'google.appengine.ext.django.backends.rdbms',
                'INSTANCE': 'trac-us:sql1',
                'NAME': 'tracdb',
                'USER': 'root',
            }
    }
else:
    # Running in development, so use a local sqlite database. Need to let gae
    # sandbox to allow us to import sqlite3.
    try:
        from google.appengine.tools.devappserver2.python import sandbox
        sandbox._WHITE_LIST_C_MODULES += ['_sqlite3']
    except:
        pass
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': join(DJANGO_ROOT, 'local', 'dev_loc.db'),
            }
    }
############################################

########## CACHE CONFIGURATION ############
# If running on appengine, use the custom cache backend that uses google's api
# with django's caching interface.
if getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    CACHES = {
            'default': {
                'BACKEND': 'backends.gae_cache.GaeMemcachedCache',
                'TIMEOUT': 300
            }
    }

# If running locally, use the dummy cache.
else:
    CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
                'TIMEOUT': 300
            }
    }
###########################################

########## GENERAL CONFIGURATION ##########
# https://docs.djangoproject.com/en/1.6/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
###########################################

########## STATIC FILES ##########
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = (
        normpath(join(DJANGO_ROOT, 'static')),
)
##################################

########## TEMPLATE CONFIGURATION ##########
TEMPLATE_DIRS = (
        normpath(join(DJANGO_ROOT, 'templates')),
)
############################################

WSGI_APPLICATION = 'main.application'
