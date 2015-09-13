# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Athlete',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('birth_date', models.DateField(null=True, blank=True)),
                ('gender', models.CharField(max_length=1, null=True, blank=True)),
                ('tfrrs_id', models.CharField(max_length=20, null=True, blank=True)),
                ('year', models.CharField(max_length=10, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Coach',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('payment', models.CharField(max_length=25, null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Reader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('id_str', models.CharField(unique=True, max_length=50)),
                ('coach', models.ForeignKey(to='trac.Coach')),
            ],
        ),
        migrations.CreateModel(
            name='Split',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.BigIntegerField()),
                ('athlete', models.ForeignKey(to='trac.Athlete')),
                ('reader', models.ForeignKey(to='trac.Reader')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_str', models.CharField(unique=True, max_length=50)),
                ('athlete', models.OneToOneField(to='trac.Athlete')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('tfrrs_code', models.CharField(unique=True, max_length=20)),
                ('coach', models.ForeignKey(to='trac.Coach')),
            ],
        ),
        migrations.CreateModel(
            name='TimingSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('stop_time', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('start_button_time', models.BigIntegerField(null=True, blank=True)),
                ('use_registered_tags_only', models.BooleanField(default=False)),
                ('private', models.BooleanField(default=True)),
                ('comment', models.CharField(max_length=2500, blank=True)),
                ('rest_time', models.IntegerField(default=0, blank=True)),
                ('track_size', models.IntegerField(default=400, blank=True)),
                ('interval_distance', models.IntegerField(default=200, blank=True)),
                ('interval_number', models.IntegerField(default=0, blank=True)),
                ('filter_choice', models.BooleanField(default=True)),
                ('coach', models.ForeignKey(to='trac.Coach')),
                ('readers', models.ManyToManyField(to='trac.Reader')),
                ('registered_tags', models.ManyToManyField(to='trac.Tag')),
                ('splits', models.ManyToManyField(to='trac.Split')),
            ],
        ),
        migrations.AddField(
            model_name='split',
            name='tag',
            field=models.ForeignKey(to='trac.Tag'),
        ),
        migrations.AddField(
            model_name='athlete',
            name='team',
            field=models.ForeignKey(blank=True, to='trac.Team', null=True),
        ),
        migrations.AddField(
            model_name='athlete',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='split',
            unique_together=set([('tag', 'time')]),
        ),
    ]
