# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import trac.models


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0008_tag_bib'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='logo',
            field=models.ImageField(null=True, upload_to=trac.models._upload_to, blank=True),
        ),
    ]
