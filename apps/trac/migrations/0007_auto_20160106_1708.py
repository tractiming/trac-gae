# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0006_auto_20151229_0305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='tfrrs_code',
            field=models.CharField(max_length=20, unique=True, null=True, blank=True),
        ),
    ]
