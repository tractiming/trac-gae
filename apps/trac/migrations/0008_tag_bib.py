# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0007_auto_20160106_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='bib',
            field=models.CharField(max_length=25, null=True, blank=True),
        ),
    ]
