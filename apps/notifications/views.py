from rest_framework import viewsets, permissions, pagination, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from notifications.models import Message, Subscription
from notifications.permissions import IsFromTaskQueuePermission
from notifications.serializers import SubscriptionSerializer
from trac.models import Split
from trac.utils.split_util import format_total_seconds


_message_template = ('TRAC update - athlete: {name}, race: {session}, '
                     'total time: {time}')


class SubscriptionViewSet(viewsets.ModelViewSet):
    """A subscription manages who receives which updates.

    Note that anyone can sign up for a subscription, but only race
    managers can edit or delete existing subscriptions.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = SubscriptionSerializer
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        """A timing session manager can view everyone subscribed to
        one of his sessions. Other users cannot view any subscription
        information.
        """
        user = self.request.user
        if user.is_anonymous():
            queryset = Subscription.objects.none()
        else:
            queryset = Subscription.objects.filter(session__coach__user=user)
        return queryset


@api_view(['post'])
@permission_classes((IsFromTaskQueuePermission,))
def notify(request):
    """Send notifications to all subscribers listening to a session.
    Each notification message includes the session name, athlete name,
    and total cumulative time.
    """
    split = Split.objects.filter(pk=request.data.get('split'),
                                 splitfilter__filtered=False).first()
    if split is not None:

        subscriptions = Subscription.objects.filter(
            session__in=split.timingsession_set.all(),
            athlete=split.athlete)

        for subscription in subscriptions:
            # Athlete must be in results since we are receiving a split
            # that says so.
            result = subscription.session.individual_results(
                athlete_ids=[subscription.athlete_id])[0]
            text = _message_template.format(
                name=result.name,
                session=subscription.session.name,
                time=format_total_seconds(result.total))
            message, created = Message.objects.get_or_create(
                subscription=subscription, message=text)
            if created:
                message.send()

    return Response(status=status.HTTP_200_OK)
