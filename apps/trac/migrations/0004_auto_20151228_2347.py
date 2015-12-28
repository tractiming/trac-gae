# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0003_auto_20151202_0413'),
    ]

    operations = [
        migrations.AddField(
            model_name='timingsession',
            name='registered_athletes',
            field=models.ManyToManyField(to='trac.Athlete'),
        ),
        migrations.AddField(
            model_name='timingsession',
            name='use_registered_athletes_only',
            field=models.BooleanField(default=False),
        ),
    ]
