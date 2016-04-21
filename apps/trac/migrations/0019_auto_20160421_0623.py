# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0018_auto_20160308_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='split',
            name='reader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='trac.Reader', null=True),
        ),
        migrations.AlterField(
            model_name='split',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='trac.Tag', null=True),
        ),
    ]
