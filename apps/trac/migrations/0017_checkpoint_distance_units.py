# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0016_auto_20160303_2353'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkpoint',
            name='distance_units',
            field=models.CharField(default=b'mi', max_length=2, choices=[(b'm', b'meters'), (b'km', b'kilometers'), (b'mi', b'miles')]),
        ),
    ]
