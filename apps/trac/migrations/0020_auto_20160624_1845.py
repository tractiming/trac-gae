# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0019_auto_20160421_0623'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coach',
            options={'verbose_name_plural': 'coaches'},
        ),
    ]
