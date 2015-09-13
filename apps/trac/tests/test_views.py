from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, force_authenticate
from trac.models import TimingSession, Reader
import trac.views
import mock
import datetime
import json


class TagViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_tags_coach(self):
        """Test that a coach can view all his athletes' tags."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/tags/', format='json')
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.data[1]['id'], 2)
        self.assertEqual(resp.status_code, 200)
    
    def test_get_tags_athlete(self):
        """Test an athlete can only view his tags."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/tags/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)


def TeamViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_teams_coach(self):
        """Test getting teams when logged in as coach."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/teams/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    def test_get_teams_athlete(self):
        """Test getting teams when logged in as athlete."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/teams/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    def test_get_teams_no_login(self):
        """Test getting teams when not logged in."""
        resp = self.client.get('/api/teams/', format='json')
        self.assertEqual(len(resp.data), 0)
        self.assertEqual(resp.status_code, 200)


class AthleteViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_athletes_coach(self):
        """Test that a coach can view all his athletes."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/athletes/', format='json')
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]['user']['username'], 'grupp')
        self.assertEqual(resp.data[1]['user']['username'], 'clevins')
        self.assertEqual(resp.status_code, 200)

    def test_get_athletes_athlete(self):
        """Test an athlete can only view himself."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/athletes/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    @mock.patch.object(trac.serializers, 'User')
    def test_pre_save(self, mock_user):
        """Test that a user is created before the athlete is."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        mock_user.objects.create.return_value = (
            User.objects.create(username='mock'))
        resp = self.client.post('/api/athletes/',
                data=json.dumps(
                    {'user': {
                        'username': 'kennyb',
                        'first_name': 'Kenenisa',
                        'last_name': 'Bekele'}
                        }), content_type='application/json')
        mock_user.objects.create.assert_called_with(
            username='kennyb', first_name='Kenenisa', last_name='Bekele')
        self.assertEqual(resp.status_code, 201)

class ReaderViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_readers_coach(self):
        """Test that a coach can view his readers."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/readers/', format='json')
        self.assertEqual(resp.data[0]['name'], "Alien 1")
        self.assertEqual(resp.data[1]['name'], "Alien 2")
        self.assertEqual(resp.status_code, 200)

    def test_get_readers_not_coach(self):
        """Test that non-coaches can't view readers."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/readers/', format='json')
        self.assertEqual(len(resp.data), 0)
        self.assertEqual(resp.status_code, 200)

    def test_pre_save(self):
        """Test that a reader is assigned to a coach before saving."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        num_readers_before = Reader.objects.filter(coach=user.coach).count()
        resp = self.client.post('/api/readers/',
                                data={'name': 'Alien 3',
                                      'id_str': 'A1013'})
        num_readers_after = Reader.objects.filter(coach=user.coach).count()
        self.assertEqual(num_readers_before+1, num_readers_after)
        self.assertEqual(resp.status_code, 201)


class ScoringViewSetTest(APITestCase):
    pass


class TimingSessionViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_sessions_coach(self):
        """Test that a coach can list his timing sessions."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/', format='json')
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    def test_pre_save(self):
        """Test that default start and stop times are used."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/',
                                data={'name': 'test_session'})
        session = TimingSession.objects.get(name='test_session')
        self.assertIsNotNone(session.start_time)
        self.assertIsNotNone(session.stop_time)
        self.assertEqual(resp.status_code, 201)
    
    def test_post_save(self):
        """Test that readers are automatically added to session."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/',
                                data={'name': 'test_session'})
        session = TimingSession.objects.get(name='test_session')
        self.assertEqual(len(session.readers.all()), 2)
        self.assertEqual(resp.status_code, 201)

    @mock.patch.object(trac.views.session_views, 'TimingSessionViewSet',
                       autospec=True)
    def test_reset(self, mock_session):
        """Test resetting a workout."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/1/reset/')
        self.assertEqual(resp.status_code, 202)
    
    @mock.patch('trac.models.TimingSession')
    def test_individual_results(self, mock_session):
        """Test retrieving individual results."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/1/individual_results/', format='json')
        self.assertEqual(resp.status_code, 200)

    @mock.patch.object(trac.views.session_views, 'timezone')
    def test_open(self, mock_timezone):
        """Test opening a session."""
        now = timezone.now().replace(microsecond=0)
        one_day_from_now = now + timezone.timedelta(days=1)
        mock_timezone.timedelta.return_value = timezone.timedelta(0)
        mock_timezone.now.return_value = now
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/1/open/')
        # This is hacky, just like our 8 second delay.
        self.assertEqual(TimingSession.objects.get(pk=1).start_time, now)
        self.assertEqual(TimingSession.objects.get(pk=1).stop_time, now)
        self.assertEqual(resp.status_code, 202)

    @mock.patch.object(trac.views.session_views, 'timezone')
    def test_close(self, mock_timezone):
        """Test closing a session."""
        now = timezone.now().replace(microsecond=0)
        mock_timezone.now.return_value = now
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/1/close/')
        self.assertEqual(TimingSession.objects.get(pk=1).stop_time, now)
        self.assertEqual(resp.status_code, 202)


class PostSplitsTest(APITestCase):

    @mock.patch.object(trac.views.reader_views, 'create_split')
    def test_post_splits(self, mock_create_split):
        """Test creating splits from reader messages."""

        mock_create_split.return_value = 0
        reader = 'A1010'
        tag = 'A0C3 0001'
        stime = timezone.now().strftime("%Y/%m/%d %H:%M:%S.%f") 
        resp = self.client.post('/api/updates/',
                                data={'r': reader,
                                      's': "[['{}', '{}'],]".format(tag, stime)})
        self.assertEqual(resp.status_code, 201)
        mock_create_split.assert_called_with(reader, tag, stime)

    @mock.patch.object(trac.views.reader_views, 'timezone')
    def test_get_server_time(self, mock_timezone):
        """Test sending the current time to the readers."""
        now = timezone.now()
        mock_timezone.now.return_value = now
        resp = self.client.get('/api/updates/')
        self.assertEqual(list(resp.data)[0], str(now))
