# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0011_auto_20160228_0144'),
    ]

    operations = [
        migrations.AddField(
            model_name='splitfilter',
            name='filtered',
            field=models.BooleanField(default=False),
        ),
    ]
