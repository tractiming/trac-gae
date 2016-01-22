import datetime
import json

from rest_framework import viewsets, permissions

from trac.models import Tag
from trac.serializers import TagSerializer
from trac.utils.user_util import is_athlete, is_coach


class TagViewSet(viewsets.ModelViewSet):
    """
    RFID tag resource.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        """
        Filter tags by requesting user.
        """
        user = self.request.user

        if is_athlete(user):
            # If the user is an athlete, display the tags he owns.
            tags = Tag.objects.filter(athlete_id=user.athlete.id)
        elif is_coach(user):
            # If the user is a coach, list the tags owned by any of his
            # athletes.
            tags = Tag.objects.filter(
                athlete__team__in=user.coach.team_set.all())
        else:
            # Otherwise, there are no tags to show.
            tags = Tag.objects.none()

        return tags
