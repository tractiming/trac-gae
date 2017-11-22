# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0005_auto_20151228_2352'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timingsession',
            name='registered_tags',
        ),
        migrations.RemoveField(
            model_name='timingsession',
            name='use_registered_tags_only',
        ),
    ]
