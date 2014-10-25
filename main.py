import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

from google.appengine.ext.webapp import util
from django.conf import settings
settings._target = None

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

