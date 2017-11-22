# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0017_checkpoint_distance_units'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='reader',
            unique_together=set([('coach', 'name')]),
        ),
    ]
