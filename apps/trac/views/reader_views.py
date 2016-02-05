import ast
import logging

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from trac.models import Reader
from trac.serializers import ReaderSerializer
from trac.utils.user_util import is_coach
from trac.utils.split_util import create_split


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
    now = timezone.now() + timezone.timedelta(seconds=8)
    return Response(now)


@csrf_exempt
@api_view(['POST','GET'])
@permission_classes((permissions.AllowAny,))
def post_splits(request):
    """
    Interacts with the readers. Readers post new splits and can get the
    current time. Readers don't handle permissions or csrf.
    """
    if request.method == 'POST':
        log.debug("Split scheme: %s", request.scheme)
        log.debug("Split data: %s", request.data)
        log.debug("Split meta: %s", request.META)
        data = request.POST
        reader_name = data['r']
        split_list = ast.literal_eval(data['s'])

        split_status = 0
        for split in split_list:
            if create_split(reader_name, split[0], split[1]):
                split_status = -1

        if split_status:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=status.HTTP_201_CREATED)

    # To avoid having to navigate between different urls on the readers, we use
    # this same endpoint to retrieve the server time.
    elif request.method == 'GET':
        # FIXME: This is a hack that offsets the delay the reader has in
        # setting its real time.  Also note that the start time is taken to be
        # the time the request hits the server, not the time the button is
        # pressed on the phone, etc.
        now = timezone.now() + timezone.timedelta(seconds=8)
        return Response({str(now)}, status.HTTP_200_OK)
