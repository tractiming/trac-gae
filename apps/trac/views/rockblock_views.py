import logging

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


log = logging.getLogger(__name__)


@api_view(['post'])
@permission_classes((permissions.AllowAny,))
def rockblock_receive(request):
    """Receive a message from a Rock Block webhook."""
    log.debug(request.data)
    return Response(status=status.HTTP_200_OK)
