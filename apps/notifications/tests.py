from collections import namedtuple

import mock
from rest_framework.test import APITestCase

import notifications.decorators
import notifications.views
from notifications.decorators import do_maybe_notification
from notifications.models import Subscription
from trac.models import (
    Athlete, Coach, TimingSession, Split, SplitFilter, User
)


class NotifyTestCase(APITestCase):

    @mock.patch.object(notifications.decorators, 'settings')
    @mock.patch.object(notifications.decorators, 'taskqueue')
    def test_task_queue_decorator(self, mock_queue, mock_settings):
        """Test the decorator that puts message tasks in the queue."""
        mock_settings.ENABLE_NOTIFICATIONS = True

        @do_maybe_notification
        def create_split():
            Splits = namedtuple('Splits', 'data')
            return Splits([{'id': 1}, {'id': 2}])

        create_split()
        mock_queue.add.assert_has_calls([
            mock.call(params={'split': 1}, url='/notifications/notify/'),
            mock.call(params={'split': 2}, url='/notifications/notify/')
        ])

    @mock.patch.object(notifications.views.Message, 'send')
    def test_notify_endpoint(self, mock_send):
        """Test sending an update message from a post to /notify."""
        coach = Coach.objects.create(
            user=User.objects.create(username='testcoach'))
        session = TimingSession.objects.create(coach=coach, name='test')
        session.start_button_time = 0
        session.save()

        athlete = Athlete.objects.create(
            user=User.objects.create(username='gjennings', first_name='Gabe',
                                     last_name='Jennings'))
        split = Split.objects.create(athlete=athlete, time=12000)
        SplitFilter.objects.create(split=split, timingsession=session)

        subscription = Subscription.objects.create(
            session=session, athlete=athlete, phone_number='+17083411935')

        resp = self.client.post('/notifications/notify/', {'split': split.pk},
                                **{'HTTP_X_APPENGINE_QUEUENAME': 'default'})
        self.assertEqual(resp.status_code, 200)
        mock_send.assert_called_once_with()
