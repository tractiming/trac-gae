# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='split',
            name='reader',
            field=models.ForeignKey(blank=True, to='trac.Reader', null=True),
        ),
        migrations.AlterField(
            model_name='split',
            name='time',
            field=models.BigIntegerField(null=True),
        ),
    ]
