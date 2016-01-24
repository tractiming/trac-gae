from rest_framework import viewsets, permissions

from trac.models import Tag
from trac.serializers import TagSerializer
from trac.utils.user_util import is_athlete, is_coach


class TagViewSet(viewsets.ModelViewSet):
    """RFID tag resource.

    An RFID tag can belong to a single athlete and be used to create
    splits. It provides a means for identifying when a particular
    athlete is seen by a reader.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        """Filter tags by requesting user.

        Athletes can see the tags assigned to them, coaches can see
        all tags owned by their athletes, anonymous users cannot
        see any tags.
        """
        user = self.request.user

        if is_athlete(user):
            tags = Tag.objects.filter(athlete_id=user.athlete.id)
        elif is_coach(user):
            tags = Tag.objects.filter(
                athlete__team__in=user.coach.team_set.all())
        else:
            tags = Tag.objects.none()

        return tags
