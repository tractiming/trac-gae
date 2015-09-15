# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0001_initial'),
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='performancerecord',
            name='timingsession',
            field=models.ForeignKey(default=0, to='trac.TimingSession'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='performancerecord',
            name='VO2',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
