# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0012_splitfilter_filtered'),
    ]

    operations = [
        migrations.AddField(
            model_name='timingsession',
            name='filter_time',
            field=models.IntegerField(default=10, blank=True),
        ),
    ]
