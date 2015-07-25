#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":

    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
        settings = "settings.common"
    else:
        settings = "settings.dev"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
