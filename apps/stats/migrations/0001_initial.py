# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerformanceRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('distance', models.IntegerField()),
                ('time', models.FloatField()),
                ('interval', models.CharField(max_length=1)),
                ('VO2', models.IntegerField(null=True, blank=True)),
                ('athlete', models.ForeignKey(to='trac.Athlete', null=True)),
                ('coach', models.ForeignKey(to='trac.Coach', null=True)),
            ],
        ),
    ]
