# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


## Add an order value to each athlete in a timing session
def add_default_order(apps, schema_editor):
    from trac.models import *
    for sess in TimingSession.objects.all():
        for idx,ath in enumerate(sess.registered_athletes.all()):
            ar = AthleteRegistration(athlete=ath, timingsession=sess, order=idx)
            ar.save()

class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0019_auto_20160421_0623'),
    ]

    operations = [
        migrations.CreateModel(
            name='AthleteRegistration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('athlete', models.ForeignKey(to='trac.Athlete')),
                ('timingsession', models.ForeignKey(to='trac.TimingSession')),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.AlterModelOptions(
            name='coach',
            options={'verbose_name_plural': 'coaches'},
        ),
        migrations.AddField(
            model_name='timingsession',
            name='registered_athletes2',
            field=models.ManyToManyField(related_name='timingsession_registered_athletes2', through='trac.AthleteRegistration', to='trac.Athlete'),
        ),
        migrations.RunPython(add_default_order),
    ]
