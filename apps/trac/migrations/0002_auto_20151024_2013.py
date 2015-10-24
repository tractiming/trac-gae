# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='primary_team',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set([('name', 'coach')]),
        ),
    ]
