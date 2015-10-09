from trac.models import Team, TimingSession, Coach
from trac.serializers import TeamSerializer, ScoringSerializer
from trac.utils.user_util import is_athlete, is_coach
from rest_framework import viewsets, permissions


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TeamSerializer
    
    def get_queryset(self):
        user = self.request.user

        if is_coach(user):
            return user.coach.team_set.filter(primary_team=True)

        elif is_athlete(user):
            return Team.objects.filter(athlete__in=[user.athlete.pk], primary_team=True)

        else:
            return Team.objects.filter(primary_team=True)

    def pre_save(self, obj):
        obj.coach = self.request.user.coach


class ScoringViewSet(viewsets.ModelViewSet):
    """
    Returns list of scored sessions
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
