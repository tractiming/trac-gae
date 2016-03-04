# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0015_timingsession_filter_max_num_splits'),
    ]

    operations = [
        migrations.CreateModel(
            name='Checkpoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('distance', models.FloatField(null=True, blank=True)),
                ('readers', models.ManyToManyField(to='trac.Reader')),
                ('session', models.ForeignKey(to='trac.TimingSession')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='checkpoint',
            unique_together=set([('name', 'session')]),
        ),
    ]
