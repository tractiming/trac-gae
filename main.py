"""
WSGI config for trac-gae project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""
import os
import django.core.handlers.wsgi

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    settings = "settings.common"
else:
    settings = "settings.dev"

os.environ["DJANGO_SETTINGS_MODULE"] = settings
application = django.core.handlers.wsgi.WSGIHandler()
