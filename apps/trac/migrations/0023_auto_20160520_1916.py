# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0022_auto_20160520_1910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timingsession',
            name='registered_athletes',
            field=models.ManyToManyField(to='trac.Athlete', through='trac.AthleteRegistration'),
        ),
    ]
