"""
WSGI config for trac-gae project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""
import os
import sys
#import django.core.handlers.wsgi

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
#os.environ["DJANGO_SETTINGS_MODULE"] = "settings.dev"
#application = django.core.handlers.wsgi.WSGIHandler()
