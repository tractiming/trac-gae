from trac.models import Athlete, Split, Team, TimingSession
from trac.serializers import AthleteSerializer
from trac.utils.user_util import random_username


def transfer_results(from_session_pk, to_session_pk):
    """Transfer race results from one account to another. Recreates all
    athletes, teams, and splits, so edits by either account will not interfere
    with the second copy of the results.
    """
    from_session = TimingSession.objects.get(pk=from_session_pk)
    to_session = TimingSession.objects.get(pk=to_session_pk)
    to_coach = to_session.coach

    teams = from_session.splits.values_list('athlete__team',
                                            'athlete__team__name').distinct()

    team_conversion = {}
    for team in teams:
        new_team, _ = Team.objects.get_or_create(coach=to_coach, name=team[1])
        team_conversion[int(team[0])] = int(new_team.id)

    for athlete_id in from_session.splits.values_list('athlete',
                                                      flat=True).distinct():
        athlete = Athlete.objects.get(pk=athlete_id)
        athlete_data = {
            'username': random_username(),
            'first_name': athlete.user.first_name,
            'last_name': athlete.user.last_name,
            'birth_date': athlete.birth_date,
            'team': team_conversion[int(athlete.team.id)]
        }
        serializer = AthleteSerializer(data=athlete_data)
        serializer.is_valid(raise_exception=True)
        new_athlete = serializer.create(serializer.validated_data)

        for split in from_session.splits.filter(
                athlete_id=athlete.id).order_by('time'):
            new_split = Split.objects.create(athlete=new_athlete,
                                             time=split.time)
            to_session.splits.add(new_split.pk)

    to_session.start_time = from_session.start_time
    to_session.stop_time = from_session.stop_time
    to_session.start_button_time = from_session.start_button_time
    to_session.filter_choice = from_session.filter_choice
    to_session.save()
