"""
Django settings for the trac-gae project.
"""
import os
import sys
from os.path import abspath, basename, dirname, join, normpath

########## PATH CONFIGURATION ##########
DJANGO_ROOT = dirname(dirname(abspath(__file__)))
SITE_ROOT = dirname(DJANGO_ROOT)
SITE_NAME = basename(DJANGO_ROOT)
sys.path.append(DJANGO_ROOT)

# Check if we are running on Appengine or Shippable.
APP_ENGINE = os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine')
SETTINGS_MODE = os.getenv('SETTINGS_MODE')
SHIPPABLE = (SETTINGS_MODE == 'test')

# Add the location of third-party libraries to the path.
if APP_ENGINE:
    sys.path.insert(0, join(DJANGO_ROOT, 'libs'))
    sys.path.insert(0, join(DJANGO_ROOT, 'libs', 'libs.zip'))

# Add the location of the apps to the path.
sys.path.insert(0, join(DJANGO_ROOT, 'apps'))
########################################

########## SECRET CONFIGURATION ##########
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gi8u=tes8q2*@@1lkfu69j^1&syc+p)l0%i0ut4$a3@5c&9b4z'
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'www.trac-us.appspot.com',
    'trac-us.appspot.com',
    'www.tracchicago.com',
    '1.trac-us.appspot.com',
    'default.trac-us.appspot.com',  # Stackdriver
    '1.trac-staging.appspot.com',
    'default.trac-staging.appspot.com',
    'trac-staging.appspot.com'
]
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
    'django.contrib.sitemaps'
)

THIRD_PARTY_APPS = (
    'rest_framework',
    'oauth2_provider',
    'rest_framework_swagger',
    'djstripe',
)


LOCAL_APPS = (
    'accounts',
    'trac',
    'website',
    'stats',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
########################################

################# TESTING ####################
if not APP_ENGINE:
    INSTALLED_APPS = INSTALLED_APPS + ('django_nose',)

    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

    NOSE_ARGS = [
        '--with-coverage', '--cover-inclusive',
        '--cover-package=trac,website,stats,accounts',
        '--exclude-dir=apps/djstripe'
    ]

if SHIPPABLE:
    NOSE_ARGS += [
        '--with-xunit', '--xunit-file=shippable/testresults/test.xml',
        '--cover-xml', '--cover-xml-file=shippable/codecoverage/coverage.xml'
    ]
##############################################

########## MIDDLEWARE CONFIGURATION ##########
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
   # 'djstripe.middleware.SubscriptionPaymentMiddleware',
)

# If running on appengine, include appstats.
if APP_ENGINE:
    MIDDLEWARE_CLASSES = (
        ('google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',)+
        MIDDLEWARE_CLASSES)

##############################################
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_MODEL_SERIALIZER_CLASS': (
        'rest_framework.serializers.ModelSerializer',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '3600/hour',
        'splits': '100/minute'
    }
}
OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope'}
}

########## URL CONFIGURATION ##########
ROOT_URLCONF = 'urls'
#######################################

########## DATABASE CONFIGURATION ##########
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
# Here we choose the backend based on whether we are running locally or in
# production. For reference, see:
# https://developers.google.com/appengine/docs/python/cloud-sql/django#development-settings
if APP_ENGINE:
    deployment_type = os.getenv('DEPLOYMENT_TYPE')

    if deployment_type == 'staging':
        sql_name = 'trac-staging:trac-staging-sql'
    else:
        sql_name = 'trac-us:sql1'

    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '/cloudsql/{}'.format(sql_name),
            'NAME': 'tracdb',
            'USER': 'root',
            'ATOMIC_REQUESTS': True,
        }
    }

elif SETTINGS_MODE in ('prod', 'stage'):
    _ip_addresses = {'prod': '173.194.82.95', 'stage': '173.194.230.143'}
    # Running in development, but want to access the Google Cloud SQL
    # instance in production or staging.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': _ip_addresses[SETTINGS_MODE],
            'NAME': 'tracdb',
            'USER': 'root',
            'PASSWORD': 'sub4mile'
        }
    }

elif SHIPPABLE:
    # Running in testing. Use the shippable settings.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test',
            'USER': 'shippable',
        }
    }

else:
    # Running in development. Try to use a mysql db if one exists on the
    # system, otherwise use a sqlite db.
    try:
        import MySQLdb
        host = 'localhost'
        user = 'trac'
        dbn = 'tracdb'

        # Uncomment the next line to force sqlite, even if mysql is configured.
        raise MySQLdb.Error

        db = MySQLdb.connect(host=host, user=user, db=dbn)
        db.close()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'HOST': host,
                'NAME': dbn,
                'USER': user,
                'ATOMIC_REQUESTS': True,
            }
        }

    except:
        # Need to let gae sandbox allow us to import sqlite3.
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
if APP_ENGINE:
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

########### STORAGE CONFIGURATION ###########
DEFAULT_FILE_STORAGE = 'backends.gae_storage.GCSStorage'
#############################################

########## TEMPLATE CONFIGURATION ##########
TEMPLATE_DIRS = (
    normpath(join(DJANGO_ROOT, 'templates')),
)
############################################

WSGI_APPLICATION = 'main.application'

########### EMAIL CONFIG ###################
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'tracchicago@gmail.com'
EMAIL_HOST_PASSWORD = 'bwemkibrtyxrksed'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
############################################

############### STRIPE API ################
STRIPE_PUBLIC_KEY = os.environ.get(
    "STRIPE_PUBLIC_KEY",
    "pk_test_CDTkwilGwFbGM1v30Sw46FtO"
)
STRIPE_SECRET_KEY = os.environ.get(
    "STRIPE_SECRET_KEY",
    "sk_test_8dwmRwbSMzZNticzW7fQaKu0"
)

DJSTRIPE_PLANS = {
    "monthly": {
        "stripe_plan_id": "Monthly",
        "name": "($99.99/month)",
        "description": "Educators only",
        "price": 9999,  # $9.99
        "currency": "usd",
        "interval": "month"
    },
    "yearly": {
        "stripe_plan_id": "Yearly",
        "name": "($1000/year)",
        "description": "Yearly educators discount",
        "price": 10000,  # $109.99
        "currency": "usd",
        "interval": "year"
    }
}

DJSTRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS = (
    'home',
    'index',
    'readers',
    'payments',
    'login',
    'register',
    'about',
    'score',
    'demo',
    'tutorial',
    'account_settings',
    'mile_demo',
    'cinci_demo',
    '(trac)',
    '(oauth2)',
)

DJSTRIPE_SEND_INVOICE_RECEIPT_EMAILS = True

###########################################

SWAGGER_SETTINGS = {
    'api_version': '0.1',
    'is_authenticated': True,
    'is_superuser': True,
    'token_type': 'Bearer',
    'exclude_namespaces': ['djstripe', 'accounts', 'stats', 'internal'],
    'info': {
        'contact': 'info@trac-us.com',
        'title': 'TRAC API',
        'description': 'Core API for managing, recording, and reporting live '
                       'race results.'
    }
}


GOOGLE_AUTH_CLIENT_ID = (
    '983021202491-kupk29qejvri4mlpd8ji0pa7r31bkrin.apps.googleusercontent.com'
)
GOOGLE_AUTH_CLIENT_SECRET = 'pszNdmSxZEIYhsC-z_BrJtop'
GOOGLE_AUTH_CLIENT_ID_IOS = (
    '983021202491-subvfv7oi83djh8vf7tkfqm6l7amg1a1.apps.googleusercontent.com'
)
GOOGLE_AUTH_CLIENT_ID_ANDROID = (
    '983021202491-3nkh0li86biqsjm7rpfgusv0pfhtnqd3.apps.googleusercontent.com'
)
GOOGLE_AUTH_DOMAINS = ['accounts.google.com', 'https://accounts.google.com']

GCS_RESULTS_BUCKET = 'trac-us.appspot.com'
GCS_RESULTS_DIR = 'results'
GCS_DEFAULT_BUCKET = 'trac-us.appspot.com'
