# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0020_auto_20160520_1900'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timingsession',
            name='registered_athletes',
        ),
    ]
