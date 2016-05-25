# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0021_remove_timingsession_registered_athletes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='timingsession',
            old_name='registered_athletes2',
            new_name='registered_athletes',
        ),
    ]
