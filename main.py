import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'settings.dev'

from google.appengine.ext.webapp import util
from django.conf import settings
settings._target = None

def main():
    application = django.core.handlers.wsgi.WSGIHandler()
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()

