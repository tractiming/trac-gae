"""
Utility script to make a static fixture file from the data in a real
timing session. This can be useful for converting a real race into a
test case.
"""
import argparse
import json
import uuid

from django.core import serializers

from trac.models import (
    TimingSession, Athlete, Reader, Checkpoint, Split, SplitFilter,
    User, Team, Tag
)


_models = [
    'timingsession', 'session', 'athlete', 'coach', 'user', 'checkpoint',
    'reader', 'split', 'splitfilter', 'team', 'tag', 'readers'
]
_exclude_fields = ['email', 'password']
_make_unique_fields = ['username', 'id_str', 'tfrrs_code']


def _random_name():
    return uuid.uuid4().hex[:30]


def serialize_timingsession(session_pk, pk_offset=0):
    """Serialize all data associated with a timing session into JSON."""
    session = TimingSession.objects.get(pk=session_pk)
    data_to_dump = [
        [session],
        [session.coach],
        [session.coach.user],
        Split.objects.filter(timingsession=session_pk),
        SplitFilter.objects.filter(timingsession=session.pk),
        Reader.objects.filter(timingsession=session_pk),
        Athlete.objects.filter(split__timingsession=session_pk),
        User.objects.filter(athlete__split__timingsession=session_pk),
        Team.objects.filter(athlete__split__timingsession=session_pk),
        Tag.objects.filter(split__timingsession=session_pk),
        Checkpoint.objects.filter(session=session_pk)
    ]

    data = []
    for item in data_to_dump:
        data.extend(json.loads(serializers.serialize('json', item)))

    for i in range(len(data)):
        data[i]['pk'] += pk_offset
        for key in data[i]['fields'].keys():
            if key in _models:
                if isinstance(data[i]['fields'][key], list):
                    data[i]['fields'][key] = [
                        (pk + pk_offset) for pk in data[i]['fields'][key]
                    ]
                else:
                    data[i]['fields'][key] += pk_offset
            elif key in _exclude_fields:
                data[i]['fields'][key] = ''
            elif key in _make_unique_fields:
                data[i]['fields'][key] = _random_name()
            elif data[i]['model'] == 'trac.reader' and key == 'name':
                data[i]['fields'][key] = _random_name()

    return data


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--session', type=int,
                        help='Dump data for the session with this ID.')
    parser.add_argument('-p', '--pk-offset', type=int, default=0,
                        help='Offset primary keys by this value.')
    parser.add_argument('-o', '--output-file',
                        help='Save the serialized data to this file.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    data = serialize_timingsession(args.session)

    with open(args.output_file, 'w') as _out:
        json.dump(data, _out, indent=4)
