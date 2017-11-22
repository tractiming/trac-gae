import logging

from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from trac.models import Reader
from trac.serializers import ReaderSerializer
from trac.utils.user_util import is_coach


log = logging.getLogger(__name__)


class ReaderViewSet(viewsets.ModelViewSet):
    """RFID reader resource.

    An RFID reader is a sensor that senses tags and assigns timestamps
    to those readings. It is used to create splits. It is owned by a
    coach and assigned to a session to indicate where the splits it
    creates should appear.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReaderSerializer

    def get_queryset(self):
        """Return only those readers belonging to the current user.

        A coach can see his own readers, other users can't see any.
        """
        user = self.request.user
        if is_coach(user):
            return Reader.objects.filter(coach=user.coach)
        else:
            return Reader.objects.none()


@api_view(['get'])
@permission_classes((permissions.AllowAny,))
def current_time(request):
    """Get the current time on the server.

    Used to sync the time on remote devices - phone, reader,
    etc.
    """
    # FIXME: This is a hack that offsets the delay the reader has in
    # setting its real time.
    now = timezone.now() + timezone.timedelta(seconds=8)
    return Response(now)
