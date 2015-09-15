"""
WSGI config for trac-gae project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""
import os
import sys

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    settings = "settings.common"

    # Add libs to path to be able to import django.
    DJANGO_ROOT = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(DJANGO_ROOT, 'libs'))
else:
    settings = "settings.dev"

os.environ["DJANGO_SETTINGS_MODULE"] = settings

import django.core.wsgi

application = django.core.wsgi.get_wsgi_application()
