import datetime
import json

import mock

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, force_authenticate

from trac.models import TimingSession, Reader, Split, Athlete, Coach
import trac.views


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
        self.assertEqual(resp.data[0]['username'], 'grupp')
        self.assertEqual(resp.data[1]['username'], 'clevins')
        self.assertEqual(resp.status_code, 200)

    def test_get_athletes_athlete(self):
        """Test an athlete can only view himself."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/athletes/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    @mock.patch.object(trac.serializers, 'timezone')
    @mock.patch.object(trac.serializers, 'UserSerializer')
    def test_pre_save(self, mock_user, mock_tz):
        """Test that a user is created before the athlete is."""
        now = timezone.now().replace(microsecond=0)
        mock_tz.now.return_value = now
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        mock_user().create.return_value = (
            User.objects.create(username='mock'))
        resp = self.client.post('/api/athletes/',
                data=json.dumps({
                    'username': 'kennyb',
                    'first_name': 'Kenenisa',
                    'last_name': 'Bekele',
                    'gender': 'M'
                }), content_type='application/json')
        mock_user().create.assert_called_with(
            mock_user().validated_data)
        self.assertEqual(resp.status_code, 201)

    def test_session_filter(self):
        """Test filtering athletes by session."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/athletes/?session=2')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 2)
        self.assertEqual(resp.status_code, 200)

    def test_delete_user(self):
        """Test that the user is deleted when the athlete is."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        athlete_user = Athlete.objects.get(pk=1).user
        resp = self.client.delete('/api/athletes/1/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(User.objects.filter(
            username=athlete_user.username).exists())


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
                                data={'name': 'Alien 5',
                                      'id_str': 'A1015'})
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
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.status_code, 200)

    def test_sessions_date_filter(self):
        """Test filtering sessions by start date."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/?'
            'start_date=2015-10-09&stop_date=2015-10-11',
            format='json')
        self.assertEqual(resp.data[0]['id'], 2)
        self.assertEqual(len(resp.data), 1)
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

    def test_reset(self):
        """Test resetting a workout."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/1/reset/')
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(TimingSession.objects.get(pk=1).splits.count(), 0)
    
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

    @mock.patch.object(trac.views.session_views, 'datetime')
    def test_start_timer(self, mock_datetime):
        """Test triggering the start button for a session."""
        now = datetime.datetime.utcnow().replace(microsecond=0)
        mock_datetime.datetime.utcnow.return_value = now
        mock_datetime.timedelta.return_value = datetime.timedelta(seconds=8)
        current_time = now-datetime.timedelta(seconds=8)
        timestamp = int((current_time-
            timezone.datetime(1970, 1, 1)).total_seconds()*1000)
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/sessions/1/start_timer/')
        self.assertEqual(TimingSession.objects.get(pk=1).start_button_time,
            timestamp)
        self.assertEqual(resp.status_code, 202)

    def test_list_order(self):
        """Test that sessions are listed in reverse chronological order."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/')
        session_ids = TimingSession.objects.all().order_by(
            '-start_time').values_list('id', flat=True) 
        self.assertEqual(
            [session['id'] for session in resp.data],
            list(session_ids))
        self.assertEqual(resp.status_code, 200)

    def test_get_by_athlete(self):
        """Test that an athlete gets all sessions he has completed."""
        user = User.objects.get(username='clevins')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/')
        completed_sessions = TimingSession.objects.filter(
            splits__athlete__user=user).distinct().order_by(
            '-start_time').values_list('id', flat=True)
        self.assertEqual(
            [session['id'] for session in resp.data],
            list(completed_sessions))
        self.assertEqual(resp.status_code, 200)

    def test_get_tfrrs_results(self):
        """Test getting tfrrs-formatted results."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/1/tfrrs/')
        self.assertEqual(resp.status_code, 200)

    def test_upload_results(self):
        """Test uploading pre-recorded splits."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        session = TimingSession.objects.create(coach=user.coach,
                                               filter_choice=False)

        athlete1 = Athlete.objects.get(user__username='clevins')
        athlete2 = Athlete.objects.get(user__username='grupp')
        split_data = [
            {'id': athlete1.id, 'splits': [20.1, 30.6, 7.6]},
            {'id': athlete2.id, 'splits': [12.4, 20.5, 31.45]}
        ]
        url = '/api/sessions/{}/upload_results/'.format(session.id)
        resp = self.client.post(url, json.dumps(split_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        results = session.individual_results()
        self.assertEqual(results[0].user_id, athlete1.id)
        self.assertEqual(results[0].splits, [20.1, 30.6, 7.6])
        self.assertEqual(results[1].user_id, athlete2.id)
        self.assertEqual(results[1].splits, [12.4, 20.5, 31.45])


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


class SplitViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_filter_splits_session(self):
        """Test filtering splits by session."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/splits/?session=1', format='json')
        self.assertEqual(resp.status_code, 200)
        session = TimingSession.objects.get(id=1) 
        self.assertEqual([split['id'] for split in resp.data],
                         list(session.splits.values_list('id', flat=True)))

    def test_filter_splits_reader(self):
        """Test filtering splits by athlete."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/splits/?reader=A1010', format='json')
        splits = Split.objects.filter(reader__id_str="A1010").values_list(
            'id', flat=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([split['id'] for split in resp.data], list(splits))

    def test_post_split(self):
        """Test creating a single split."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/splits/',
            data=json.dumps({'reader': 'A1010',
                             'athlete': 1,
                             'time': 1234,
                             'tag': None,
                             'sessions': []}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        new_split = Split.objects.filter(time=1234, athlete=1,
                                         reader__id_str='A1010')
        self.assertTrue(new_split.exists())

    def test_post_splits_bulk(self):
        """Test creating many splits at once."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/splits/',
            data=json.dumps([
                {'reader': 'A1010',
                 'athlete': 1,
                 'time': 1234,
                 'tag': None,
                 'sessions': []},
                {'reader': 'A1010',
                 'athlete': 2,
                 'time': 1235,
                 'tag': None,
                 'sessions': []},
            ]),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        new_split_1 = Split.objects.filter(time=1234, athlete=1,
                                         reader__id_str='A1010')
        new_split_2 = Split.objects.filter(time=1235, athlete=2,
                                         reader__id_str='A1010')
        self.assertTrue(new_split_1.exists())
        self.assertTrue(new_split_2.exists())

    def test_post_split_active_readers(self):
        """Test that new splits are added to active sessions."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        session = TimingSession.objects.get(pk=1)
        session.start_time = timezone.now()
        session.stop_time = timezone.now() + timezone.timedelta(days=1)
        session.save()
        resp = self.client.post('/api/splits/',
            data=json.dumps({'reader': 'A1010',
                             'athlete': 1,
                             'time': 1234,
                             'tag': None,
                             'sessions': []}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        new_split = session.splits.filter(time=1234, athlete=1,
                                          reader__id_str='A1010')
        self.assertTrue(new_split.exists())


class UserViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_me(self):
        """Test that /users/me is aliased to the current user."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/users/me/', format='json')
        self.assertEqual(resp.data['username'], 'alsal')
        self.assertEqual(resp.data['first_name'], 'Alberto')
        self.assertEqual(resp.data['last_name'], 'Salazar')
        self.assertEqual(resp.status_code, 200)

    def test_list_users(self):
        """Test that listing users returns only the current user."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/users/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['username'], 'alsal')
        self.assertEqual(resp.data[0]['first_name'], 'Alberto')
        self.assertEqual(resp.data[0]['last_name'], 'Salazar')
        self.assertEqual(resp.status_code, 200)

    def test_change_password(self):
        """Test changing a user's password."""
        user = User.objects.get(username='alsal')
        user.set_password('oldpassword')
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/users/me/change_password/',
                                format='json',
                                data={'old_password': 'oldpassword',
                                      'new_password': 'newpassword'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(user.check_password('newpassword'))

    def test_tutorial_limiter(self):
        """Test whether to display tutorial."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/users/me/tutorial_limiter/',
                               format='json')
        # Database is created when test is run, so should return True.
        self.assertTrue(resp.data['show_tutorial'])
        self.assertEqual(resp.status_code, 200)

class AuthTestCase(TestCase):

    def setUp(self):
        self.user_data = {
            'username': 'newuser',
            'password': 'password',
            'email': 'email@gmail.com',
            'user_type': None
        }

    @mock.patch.object(trac.views.auth_views, 'send_mail')
    def test_register_athlete(self, mock_mail):
        """Test registering an athlete."""
        self.user_data['user_type'] = 'athlete'
        resp = self.client.post('/api/register/',
                                data=json.dumps(self.user_data),
                                content_type='application/json')
        self.assertTrue(Athlete.objects.get(user__username="newuser"))
        self.assertEqual(resp.status_code, 201)

    @mock.patch.object(trac.views.auth_views, 'send_mail')
    def test_register_coach(self, mock_mail):
        """Test registering a coach."""
        self.user_data['user_type'] = 'coach'
        resp = self.client.post('/api/register/',
                                data=json.dumps(self.user_data),
                                content_type='application/json')
        self.assertTrue(Coach.objects.get(user__username="newuser"))
        self.assertEqual(resp.status_code, 201)
