# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def determine_split_filters(apps, schema_editor):
    """Determine whether each split should be designated as filtered. New,
    incoming splits are automatically filtered, but this function will
    apply the filter to splits that are already in the database.

    Note that this is the same code as found in
    `SplitFilter.determine_filter`. It is copied here since custom model
    methods are not available during the migration.
    """
    SplitFilter = apps.get_model('trac', 'SplitFilter')
    for split in SplitFilter.objects.all():
        session = split.timingsession
        most_recent_time = session.splits.filter(
            athlete=split.split.athlete,
            time__lt=split.split.time).aggregate(
            models.Max('time'))['time__max']

        if most_recent_time is None:
            most_recent_time = session.start_button_time
        if most_recent_time is not None:
            min_seconds = 1000*session.filter_time
            filter_ = (split.split.time - most_recent_time) < min_seconds
        else:
            filter_ = False

        split.filtered = filter_
        split.save()

def reverse_determine_split_filters(apps, schema_editor):
    """Reverse applying the filter to every split by setting all splits
    as unfiltered.
    """
    SplitFilter = apps.get_model('trac', 'SplitFilter')
    SplitFilter.objects.all().update(filtered=False)


class Migration(migrations.Migration):

    dependencies = [
        ('trac', '0013_timingsession_filter_time'),
    ]

    operations = [
        migrations.RunPython(
            determine_split_filters,
            reverse_code=reverse_determine_split_filters),
    ]
