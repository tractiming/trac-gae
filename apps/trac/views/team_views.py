from rest_framework import viewsets, permissions, filters

from trac.filters import TeamFilter
from trac.models import Team, TimingSession, Coach
from trac.serializers import TeamSerializer, ScoringSerializer
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

    def pre_save(self, obj):
        # Associate team with current user.
        obj.coach = self.request.user.coach


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
