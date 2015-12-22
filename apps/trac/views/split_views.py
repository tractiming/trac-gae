from django.db.models import Q
from rest_framework import (
    viewsets, permissions, status, pagination, filters
)
from rest_framework.response import Response

from trac.filters import SplitFilter
from trac.models import Split
from trac.serializers import SplitSerializer


class SplitViewSet(viewsets.ModelViewSet):
    """
    Split resource.
    """
    serializer_class = SplitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SplitFilter

    def get_queryset(self):
        """Filter splits by athlete, session, tag or time."""
        return Split.objects.all()

    def create(self, request, *args, **kwargs):
        # https://stackoverflow.com/questions/22881067/
        # django-rest-framework-post-array-of-objects
        is_many = isinstance(request.data, list)
        if not is_many:
            return super(SplitViewSet, self).create(request, *args, **kwargs)
        else:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
