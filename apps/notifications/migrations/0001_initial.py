# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0008_tag_bib'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=200)),
                ('sent_time', models.DateTimeField()),
                ('success', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone_number', models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(regex=b'^\\+?1?\\d{9,15}$')])),
                ('athlete', models.ForeignKey(to='trac.Athlete')),
                ('session', models.ForeignKey(to='trac.TimingSession')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='subscription',
            field=models.ForeignKey(to='notifications.Subscription'),
        ),
    ]
