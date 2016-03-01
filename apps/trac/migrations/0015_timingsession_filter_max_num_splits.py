# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0014_auto_20160229_0533'),
    ]

    operations = [
        migrations.AddField(
            model_name='timingsession',
            name='filter_max_num_splits',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
