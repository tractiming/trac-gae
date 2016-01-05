import logging

from dateutil import parser
from django.db.models import Q
from django.utils import timezone
from rest_framework import (
    viewsets, permissions, status, pagination, filters
)
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from trac.filters import SplitFilter
from trac.models import Split
from trac.serializers import SplitSerializer


log = logging.getLogger(__name__)


_EPOCH = timezone.datetime(1970, 1, 1)


def _parse_split_time(split):
    """Convert a split's time into a timestamp."""
    try:
        time = split['time']
    except KeyError:
        return None

    if isinstance(time, (str, unicode)):
        parsed_time = parser.parse(time)
        timestamp = int((parsed_time - _EPOCH).total_seconds() * 1000)
        split['time'] = timestamp


def _convert_times(data):
    """Parse times for every split in an incoming request."""
    if not isinstance(data, list):
        _parse_split_time(data)
    else:
        for split in data:
            _parse_split_time(split)


class SplitViewSet(viewsets.ModelViewSet):
    """
    Split resource.
    """
    serializer_class = SplitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SplitFilter

    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'splits'

    def get_queryset(self):
        """Filter splits by athlete, session, tag or time."""
        return Split.objects.all()

    def create(self, request, *args, **kwargs):
        # https://stackoverflow.com/questions/22881067/
        # django-rest-framework-post-array-of-objects
        log.debug("Creating split(s): %s", request.data)
        log.debug("Create split meta: %s", request.META)
        _convert_times(request.data)
        is_many = isinstance(request.data, list)
        if not is_many:
            return super(SplitViewSet, self).create(request, *args, **kwargs)
        else:
            serializer = self.get_serializer(data=request.data, many=True)
            if not serializer.is_valid(raise_exception=False):
                # Readers can post a list of splits in a single request. If
                # one split in the list is not valid, we should still save the
                # others. The following block runs validation twice. After the
                # first validation, bad splits are removed from the list so
                # that the second serializer contains only valid splits.
                clean_objects = [
                    data for i, data in enumerate(serializer.initial_data)
                    if not serializer.errors[i]
                ]

                # The response status is ambiguous if there are some objects
                # that did not validate and some that did. We choose to return
                # a 201 if any objects were created and a 400 if none of the
                # splits could be validated.
                if not clean_objects:
                    raise ValidationError(serializer.errors)

                serializer = self.get_serializer(data=clean_objects,
                                                 many=True)
                serializer.is_valid(raise_exception=True)

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
