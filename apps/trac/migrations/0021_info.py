# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0020_auto_20160624_1845'),
    ]

    operations = [
        migrations.CreateModel(
            name='Info',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('info', models.CharField(max_length=250, blank=True)),
                ('athlete', models.ForeignKey(to='trac.Athlete')),
                ('timingsession', models.ForeignKey(to='trac.TimingSession')),
            ],
        ),
    ]
