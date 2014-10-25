import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "settings.dev"

from google.appengine.ext.webapp import util
from django.conf import settings
#settings._target = None

import django.core.handlers.wsgi

from django.conf import settings
#print settings.SECRET_KEY
application = django.core.handlers.wsgi.WSGIHandler()

