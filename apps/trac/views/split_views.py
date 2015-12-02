from django.db.models import Q
from rest_framework import viewsets, permissions, status, pagination
from trac.serializers import SplitSerializer
from trac.models import Split


class SplitViewSet(viewsets.ModelViewSet):
    """
    Split resource.
    """
    serializer_class = SplitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        """Filter splits by athlete, session, tag or time."""
        user = self.request.user
        filters = Q()

        session = self.request.GET.get('session')
        reader = self.request.GET.get('reader')
        tag = self.request.GET.get('tag')
        athlete = self.request.GET.get('athlete')
        time_lte = self.request.GET.get('time_lte')
        time_gte = self.request.GET.get('time_gte')

        if session is not None:
            filters &= Q(timingsession=int(session))
        if reader is not None:
            filters &= Q(reader__id_str=reader)
        if session is not None:
            filters &= Q(tag__id_str=tag)
        if athlete is not None:
            filters &= Q(athlete=int(athlete))
        if time_lte is not None:
            filters &= Q(time__lte=int(time_lte))
        if time_gte is not None:
            filters &= Q(time__gte=int(time_gte))

        return Split.objects.filter(filters)
