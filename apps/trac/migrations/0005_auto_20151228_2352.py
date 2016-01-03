# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def registered_tags_to_athletes(apps, schema_editor):
    """Convert `registered_tags` to `registered_athletes`."""
    TimingSession = apps.get_model('trac', 'TimingSession')
    for session in TimingSession.objects.all():
        athlete_ids = session.registered_tags.values_list(
            'athlete_id', flat=True).distinct()
        for athlete in athlete_ids:
            session.registered_athletes.add(athlete)
        session.save()


def reverse_registered_tags_to_athletes(apps, schema_editor):
    """Reverse `registered_tags` to `registered_athletes`
    conversion.
    """
    TimingSession = apps.get_model('trac', 'TimingSession')
    for session in TimingSession.objects.all():
        session.registered_athletes.clear()
        session.save()


def use_registered_tags_to_athletes(apps, schema_editor):
    """Convert the `use_registered_tags_only` field to
    `use_registered_athletes_only`.
    """
    TimingSession = apps.get_model('trac', 'TimingSession')
    for session in TimingSession.objects.all():
        session.use_registered_athletes_only = (
            session.use_registered_tags_only)
        session.save()


def reverse_use_registered_tags_to_athletes(apps, schema_editor):
    """Reverse the conversion os `use_registered_tags_only` field to
    `use_registered_athletes_only` by setting the field to False
    (the default).
    """
    TimingSession = apps.get_model('trac', 'TimingSession')
    TimingSession.objects.all().update(use_registered_athletes_only=False)


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0004_auto_20151228_2347'),
    ]

    operations = [
        migrations.RunPython(
            registered_tags_to_athletes,
            reverse_code=reverse_registered_tags_to_athletes),
        migrations.RunPython(
            use_registered_tags_to_athletes,
            reverse_code=reverse_use_registered_tags_to_athletes),
    ]
