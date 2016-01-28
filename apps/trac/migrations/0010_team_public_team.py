# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0009_team_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='public_team',
            field=models.BooleanField(default=False),
        ),
    ]
