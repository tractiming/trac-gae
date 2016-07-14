# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='performancerecord',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='performancerecord',
            name='event_name',
            field=models.CharField(default=django.utils.datetime_safe.datetime.now, max_length=100),
            preserve_default=False,
        ),
    ]
