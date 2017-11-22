"""
Utilities for outputing results in TFRRS format.
"""
from collections import defaultdict, OrderedDict

from django.core.exceptions import ObjectDoesNotExist

from trac.models import Athlete, Tag


_TFRRS_FIELDS = [
    'bib', 'TFFRS_ID', 'team_name', 'team_code', 'first_name', 'last_name',
    'gender', 'year', 'date_of_birth', 'event_code', 'event_name',
    'event_division', 'event_min_age', 'event_max_age', 'sub_event_code',
    'mark', 'metric', 'fat', 'place', 'score', 'heat', 'heat_place', 'rnd',
    'points', 'wind', 'relay_squad'
]


def format_tfrrs_results(session):
    """Given a session, generate raw results using
    `TimingSession.individual_results` and create a list of ordered
    dicts, each containing a row of a TFRRS-formatted CSV file.
    """
    raw_results = session.individual_results()

    results = []
    for num, result in enumerate(raw_results):

        athlete = Athlete.objects.get(pk=result.user_id)
        team = result.team.name
        birth_date = athlete.birth_date

        try:
            tag = Tag.objects.get(athlete=athlete)
            bib = tag.id_str
        except ObjectDoesNotExist:
            bib = None

        if athlete.birth_date is not None:
            birth_date = birth_date.strftime('%Y-%m-%d')
        else:
            birth_date = None

        data = {
            'bib': bib,
            'TFFRS_ID': athlete.tfrrs_id,
            'place': num + 1,
            'score': num + 1,
            'mark': result.total,
            'team_name': result.team.name,
            'team_code': result.team.tfrrs_code,
            'first_name': athlete.user.first_name,
            'last_name': athlete.user.last_name,
            'gender': athlete.gender,
            'metric': 1,
            'date_of_birth': birth_date,
            'event_code': session.interval_distance,
            'event_name': session.name,
            'fat': 0
        }

        row = {key: str(value) for key, value in data.items()
               if value is not None}
        row = defaultdict(str, row)
        results.append(
            OrderedDict((field, row[field]) for field in _TFRRS_FIELDS))

    return results
