from rest_framework import viewsets, permissions, filters, status, mixins
from rest_framework.decorators import detail_route
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from django.utils.dateparse import parse_date

from trac.filters import TeamFilter
from trac.models import Team, TimingSession, Coach, Athlete
from trac.serializers import (
    TeamSerializer, ScoringSerializer, AthleteSerializer, TagSerializer
)
from trac.utils.user_util import is_athlete, is_coach
from trac.validators import roster_upload_validator


class TeamViewSet(viewsets.ModelViewSet):
    """Team resource.

    A team is managed by a coach and contains a group of athletes.
    ---
    partial_update:
      omit_parameters:
      - query
      parameters_strategy: replace
      parameters:
        - name: logo
          description: Team logo
          type: file
          paramType: form
    create:
      omit_parameters:
      - query
      parameters_strategy: replace
      parameters:
        - name: logo
          description: Team logo
          type: file
          paramType: form
    update:
      omit_parameters:
      - query
      parameters_strategy: replace
      parameters:
        - name: logo
          description: Team logo
          type: file
          paramType: form
    retrieve:
      omit_parameters:
      - query
    list:
      parameters_strategy: merge
      parameters:
        - name: primary_team
          paramType: query
          description: Primary team
          type: boolean
    destroy:
      omit_parameters:
      - query
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = TeamSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TeamFilter

    def get_queryset(self):
        """Filter teams based on current user.

        A coach can see all of the teams he owns, an athlete can see
        all of the teams he belongs to, an anonymous user can see
        teams that are designated public and primary.
        """
        user = self.request.user

        if is_coach(user):
            return user.coach.team_set.all()
        elif is_athlete(user):
            return Team.objects.filter(athlete__in=[user.athlete.pk],
                                       primary_team=True)
        else:
            return Team.objects.filter(public_team=True, primary_team=True)

    # first_name,last_name,rfid_code,new_bday,new_gender,new_first_name,new_last_name
    @detail_route(methods=['post'], parser_classes=(FileUploadParser,))
    def upload_new_names(self, request, *args, **kwargs):
        csv_data = roster_upload_validator(request.data)
        for row in csv_data:
            # find athlete
            try:
                athlete = Athlete.objects.get(user__first_name=row['first_name'],
                                              user__last_name=row['last_name'],
                                              tag__id_str=row['rfid_code'])
            except (ValueError, ObjectDoesNotExist):
                return Response("Could not find athlete with matching"
                                "first_name={}, last_name={}, and rfid_tag={}".format(row['first_name', row['last_name'], row['rfid_code']]),
                                status=status.HTTP_400_BAD_REQUEST)

            #update name
            athlete.user.first_name = row['new_first_name']
            athlete.user.last_name = row['new_last_name']
            athlete.birth_date = parse_date(row['new_bday'])
            athlete.gender = row['new_gender']
            athlete.save()
            athlete.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], parser_classes=(FileUploadParser,))
    def upload_roster(self, request, *args, **kwargs):
        """Upload a CSV file with athletes on this team.

        The uploaded file must have a header row that contains the
        fields "first_name" and "last_name" and may additionally
        contain any of the fields "gender" or "birth_date".

        A new athlete will be created for each row in the file and that
        athlete will be assigned to the current team.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        parameters:
        - name: file
          description: CSV file with roster information
          type: file
        """
        team = self.get_object()
        roster = roster_upload_validator(request.data)

        for athlete in roster:
            athlete_data = {
                'first_name': athlete['first_name'],
                'last_name': athlete['last_name'],
                'gender': athlete.get('gender', None),
                'birth_date': athlete.get('birth_date', '').strip() or None,
                'tfrrs_id': athlete.get('tfrrs_id', None),
                'team': team.pk
            }
            serializer = AthleteSerializer(data=athlete_data)
            serializer.is_valid(raise_exception=True)
            new_athlete = serializer.create(serializer.validated_data)

            rfid_code = athlete.get('rfid_code', None) or None
            bib_number = athlete.get('bib_number', None) or None
            if rfid_code is not None:
                tag_data = {
                    'bib': bib_number,
                    'id_str': rfid_code,
                    'athlete': new_athlete.pk
                }
                serializer = TagSerializer(data=tag_data)
                serializer.is_valid(raise_exception=True)
                serializer.create(serializer.validated_data)

        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: Merge with GET /sessions
class ScoringViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
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
            coach = Team.objects.get(id=team).coach
            sessions = TimingSession.objects.filter(private=False, coach=coach)
        else:
            # return all public sessions
            sessions = TimingSession.objects.filter(private=False)

        return sessions
