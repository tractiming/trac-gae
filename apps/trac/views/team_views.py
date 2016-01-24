import csv
import uuid

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import detail_route
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response

from trac.filters import TeamFilter
from trac.models import Team, TimingSession, Coach
from trac.serializers import (
    TeamSerializer, ScoringSerializer, AthleteSerializer
)
from trac.utils.user_util import is_athlete, is_coach


class TeamViewSet(viewsets.ModelViewSet):
    """
    Team resource.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = TeamSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TeamFilter

    def get_queryset(self):
        user = self.request.user

        if is_coach(user):
            return user.coach.team_set.all()

        elif is_athlete(user):
            return Team.objects.filter(athlete__in=[user.athlete.pk],
                                       primary_team=True)

        else:
            return Team.objects.filter(primary_team=True)

    @detail_route(methods=['post'], parser_classes=(FileUploadParser,))
    def upload_roster(self, request, *args, **kwargs):
        """Upload a CSV file with athletes on this team.

        The uploaded file must have a header row that contains the
        fields "first_name" and "last_name" and may additionally
        contain any of the fields "gender" or "birth_date".

        A new athlete will be created for each row in the file and that
        athlete will be assigned to the current team.
        """
        team = self.get_object()
        file_obj = request.data.pop('file', None)

        if not file_obj:
            return Response("No file uploaded",
                            status=status.HTTP_400_BAD_REQUEST)
        file_obj = file_obj[0]

        roster = csv.DictReader(file_obj)
        if not all(field in roster.fieldnames for field in
                   ('first_name', 'last_name')):
            return Response('File does not contain "first_name" and '
                            '"last_name" in header',
                            status=status.HTTP_400_BAD_REQUEST)

        for athlete in roster:
            athlete_data = {
                'username': uuid.uuid4().hex[:30],  # Assign random username
                'first_name': athlete['first_name'],
                'last_name': athlete['last_name'],
                'gender': athlete.get('gender', None),
                'birth_date': athlete.get('birth_date', None),
                'team': team.pk
            }
            serializer = AthleteSerializer(data=athlete_data)
            serializer.is_valid(raise_exception=True)
            serializer.create(serializer.validated_data)

        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: Merge with GET /sessions
class ScoringViewSet(viewsets.ModelViewSet):
    """
    Resource of publicly scored sessions.
    """
    serializer_class = ScoringSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """
        Overrides default method to filter public sessions by organization.
        """
        team = self.request.GET.get('team', None)
        if team == 'Unaffiliated':
            # return sessions belonging to unaffiliated users
            coaches = Coach.objects.filter(team__isnull=True)
            sessions = TimingSession.objects.filter(private=False,
                                                    coach__in=coaches)
        elif team is not None:
            # return sessions belonging to users under requested organization
            coach = Team.objects.get(name=team).coach
            sessions = TimingSession.objects.filter(private=False, coach=coach)
        else:
            # return all public sessions
            sessions = TimingSession.objects.filter(private=False)

        return sessions
