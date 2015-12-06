# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0002_auto_20151024_2013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='split',
            name='reader',
            field=models.ForeignKey(blank=True, to='trac.Reader', null=True),
        ),
        migrations.AlterField(
            model_name='split',
            name='tag',
            field=models.ForeignKey(blank=True, to='trac.Tag', null=True),
        ),
    ]
