# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0010_team_public_team'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='SplitFilter',
                    fields=[
                        ('id', models.AutoField(verbose_name='ID',
                                                serialize=False,
                                                auto_created=True,
                                                primary_key=True)),
                        ('split', models.ForeignKey(to='trac.Split')),
                    ],
                    options={
                        'db_table': 'trac_timingsession_splits',
                    },
                ),
                migrations.AlterField(
                    model_name='timingsession',
                    name='splits',
                    field=models.ManyToManyField(to='trac.Split',
                                                 through='trac.SplitFilter'),
                ),
                migrations.AddField(
                    model_name='splitfilter',
                    name='timingsession',
                    field=models.ForeignKey(to='trac.TimingSession'),
                ),
                migrations.AlterUniqueTogether(
                    name='splitfilter',
                    unique_together=set([('timingsession', 'split')]),
                ),
            ],
            database_operations=[]
        )
    ]
