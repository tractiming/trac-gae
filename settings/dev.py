from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SWAGGER_SETTINGS['is_superuser'] = False
SWAGGER_SETTINGS['is_authenticated'] = False
GCS_RESULTS_DIR = 'results/test'
MEDIA_ROOT = 'media/test'
#ENABLE_NOTIFICATIONS = True
