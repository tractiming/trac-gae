import datetime
import json
import tempfile
from collections import OrderedDict

import mock
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APITestCase

import trac.views
from trac.models import (
    TimingSession, Reader, Split, Athlete, Coach, Team, Tag, Checkpoint,
    SplitFilter
)


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


class TeamViewSetTest(APITestCase):

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
        #self.assertEqual(resp.data[0]['id'], 1)
        self.assertEqual(resp.status_code, 200)

    def test_create_team(self):
        """Test creating a team and assigning to a coach."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/teams/',
            data=json.dumps({'name': 'my team'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        team = Team.objects.get(pk=resp.data['id'])
        self.assertEqual(team.coach.user.username, 'alsal')

    def test_roster_upload_no_birthdate(self):
        """Test uploading a roster with a blank "birth_date" column."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='r+w') \
                as _roster:
            _roster.write('first_name,last_name,birth_date\n'
                          'Ryan,Hall,')
            _roster.seek(0)
            resp = self.client.post('/api/teams/1/upload_roster/',
                                    data={'file': [_roster]})
            self.assertEqual(resp.status_code, 204)
        team = Team.objects.get(pk=1)
        self.assertTrue(team.athlete_set.filter(
            user__first_name='Ryan',
            user__last_name='Hall').exists())


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
        athlete_username = Athlete.objects.get(pk=1).user.username
        resp = self.client.delete('/api/athletes/1/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(User.objects.filter(
            username=athlete_username).exists())

    def test_create_tag(self):
        """Test creating a new tag with the user."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/athletes/',
            data=json.dumps({
                'username': 'mwithrow',
                'tag': '1234'
            }),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Athlete.objects.filter(user__username='mwithrow').exists())
        self.assertTrue(Tag.objects.filter(id_str='1234').exists())
        self.assertEqual(
            Tag.objects.get(id_str='1234').athlete.user.username,
            'mwithrow')

    def test_update_tag(self):
        """Test updating a user's tag."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)

        # Overwrite an existing tag.
        resp = self.client.patch(
            '/api/athletes/1/',
            data=json.dumps({'tag': '1234'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['tag'], '1234')

        # Clear the tag.
        resp = self.client.patch(
            '/api/athletes/1/',
            data=json.dumps({'tag': None}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['tag'], None)

        # Try to post an existing tag and fail.
        resp = self.client.patch(
            '/api/athletes/1/',
            data=json.dumps({'tag': 'AAAA 0002'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    @mock.patch.object(trac.serializers, 'random_username')
    def test_create_without_username(self, mock_name):
        """Test that random username is generated if no username given."""
        mock_name.return_value = 'superrandomname'
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/athletes/',
            data=json.dumps({
                'first_name': 'Sam',
                'last_name': 'Chelenga',
            }), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(mock_name.called)
        self.assertTrue(Athlete.objects.filter(
            user__username='superrandomname').exists())


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

    @mock.patch.object(trac.views.reader_views, 'timezone')
    def test_get_current_time(self, mock_timezone):
        """Test sending the current time to the readers."""
        now = timezone.now() + timezone.timedelta(seconds=8)
        mock_timezone.now.return_value = now
        mock_timezone.timedelta.return_value = timezone.timedelta(seconds=0)
        resp = self.client.get('/api/time/')
        self.assertEqual(resp.data, now)


class ScoringViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_edit_not_allowed(self):
        """Test that sessions cannot be edited through the score endpoint."""
        resp = self.client.patch('/api/score/1/', data={'name': 'can edit'})
        self.assertEqual(resp.status_code, 405)  # Method not allowed


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
        resp = self.client.get('/api/sessions/1/individual_results/',
                               format='json')
        self.assertEqual(resp.status_code, 200)

    def test_edit_denied_public_session(self):
        """Test that unauthenticated users can't edit a session."""
        resp = self.client.patch('/api/sessions/1/',
                                 data={'name': 'edited name'})
        self.assertEqual(resp.status_code, 401)

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
        mock_datetime.timedelta.return_value = datetime.timedelta(seconds=0)
        current_time = now
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

    def test_register_athletes(self):
        """Test appending to registered athletes list."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/register_athletes/',
            data=json.dumps({'athletes': [1, 2]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        session = TimingSession.objects.get(pk=1)
        self.assertEqual(
            list(session.registered_athletes.values_list('id', flat=True)),
            [1, 2])

    def test_remove_athletes(self):
        """Test removing from registered athletes list."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/register_athletes/',
            data=json.dumps({'athletes': [1, 2]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            '/api/sessions/1/remove_athletes/',
            data=json.dumps({'athletes': [2]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        session = TimingSession.objects.get(pk=1)
        self.assertEqual(
            list(session.registered_athletes.values_list('id', flat=True)),
            [1])

    @mock.patch.object(trac.views.session_views, 'csv')
    @mock.patch.object(trac.views.session_views, 'get_public_link')
    @mock.patch.object(trac.views.session_views, 'gcs_writer')
    def test_export_results_csv(self, mock_writer, mock_link, mock_csv):
        """Test saving a results file in GCS."""
        mock_link.return_value = 'filedownloadurl.csv'
        results_path = '{}/1/individual.csv'.format(settings.GCS_RESULTS_DIR)
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/export_results/',
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        mock_writer.assert_called_with(settings.GCS_RESULTS_BUCKET,
                                       results_path, make_public=True)
        mock_csv.DictWriter().writerow.assert_has_calls([
            mock.call({'Name': 'Cam Levins', 'Time': '05:18.601'}),
            mock.call({'Name': 'Galen Rupp', 'Time': '06:29.045'})])
        self.assertEqual(resp.data['uri'], 'filedownloadurl.csv')

    @mock.patch.object(trac.views.session_views, 'csv')
    @mock.patch.object(trac.views.session_views, 'get_public_link')
    @mock.patch.object(trac.views.session_views, 'gcs_writer')
    def test_export_csv_with_splits(self, mock_writer, mock_link, mock_csv):
        """Test saving a results file in GCS that includes all splits."""
        mock_link.return_value = 'filedownloadurl.csv'
        results_path = '{}/1/individual-splits.csv'.format(
            settings.GCS_RESULTS_DIR)
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/export_results/',
            data=json.dumps({'results_type': 'splits'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        mock_writer.assert_called_with(settings.GCS_RESULTS_BUCKET,
                                       results_path, make_public=True)
        mock_csv.DictWriter().writerow.assert_has_calls([
            mock.call(OrderedDict((
                ('Name', 'Cam Levins'),
                ('Interval 1', 123.021),
                ('Interval 2', 195.58),
                ('Total', '05:18.601')))),
            mock.call(OrderedDict((
                ('Name', 'Galen Rupp'),
                ('Interval 1', 122.003),
                ('Interval 2', 197.237),
                ('Interval 3', 69.805),
                ('Total', '06:29.045'))))])
        self.assertEqual(resp.data['uri'], 'filedownloadurl.csv')

    @mock.patch.object(trac.views.session_views, 'write_pdf_results')
    @mock.patch.object(trac.views.session_views, 'get_public_link')
    @mock.patch.object(trac.views.session_views, 'gcs_writer')
    def test_export_results_pdf(self, mock_writer, mock_link, mock_pdf):
        """Test saving results in a PDF file."""
        mock_link.return_value = 'filedownloadurl.pdf'
        results_path = '{}/1/individual.pdf'.format(settings.GCS_RESULTS_DIR)
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/export_results/',
            data=json.dumps({'file_format': 'pdf'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        mock_writer.assert_called_with(settings.GCS_RESULTS_BUCKET,
                                       results_path, make_public=True)
        results = (
            OrderedDict((('Name', 'Cam Levins'), ('Time', '05:18.601'))),
            OrderedDict((('Name', 'Galen Rupp'), ('Time', '06:29.045')))
        )
        mock_pdf.assert_called_with(mock_writer().__enter__(), mock.ANY)
        self.assertEqual(results, tuple(mock_pdf.call_args_list[0][0][1]))
        self.assertEqual(resp.data['uri'], 'filedownloadurl.pdf')

    @mock.patch.object(trac.views.session_views.TimingSessionViewSet,
                       'export_results')
    @mock.patch.object(trac.views.session_views, 'send_mass_mail')
    def test_send_email(self, mock_send, mock_export):
        """Test sending emails with results."""
        mock_export().data = {'uri': 'linktofile.csv'}
        mock_export().status_code = 200
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/email_results/',
            data=json.dumps({'full_results': True}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(mock_export.called)
        mock_send.assert_called_with([('60 x 400m', mock.ANY,
                                      'tracchicago@gmail.com',
                                      ['grupp@nike.com'])],
                                     fail_silently=False)

    def test_individual_results_athletes(self):
        """Test getting results only for certain athletes."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/1/individual_results/?'
                               'athletes=1,2112', format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['num_returned'], 1)
        self.assertEqual(resp.data['results'][0]['id'], 1)

    def test_individual_results_first_seen(self):
        """Test getting the first time an athlete was seen."""
        coach = Coach.objects.get(user__username='alsal')
        session = TimingSession.objects.create(coach=coach, name='test')
        self.client.force_authenticate(user=coach.user)
        split_time = '2015/01/01 01:01:01.123'
        self.client.post(
            '/api/splits/',
            data=json.dumps({
                'reader': None,
                'athlete': 1,
                'time': split_time,
                'tag': None,
                'sessions': [session.pk]}),
            content_type='application/json')
        resp = self.client.get('/api/sessions/{}/individual_results/'
                               '?athletes=1'.format(session.pk),
                               format='json')
        self.assertEqual(resp.data['results'][0]['first_seen'], split_time)

    def test_individual_results_first_seen_start_button(self):
        """Test the case where the first seen time is the start button."""
        coach = Coach.objects.get(user__username='alsal')
        session = TimingSession.objects.create(coach=coach, name='test')

        start_time = '2015/01/01 01:01:01.123'
        stamp = timezone.datetime.strptime(start_time, '%Y/%m/%d %H:%M:%S.%f')
        epoch = timezone.datetime(1970, 1, 1)
        session.start_button_time = int((stamp-epoch).total_seconds()*1000)
        session.save()

        self.client.force_authenticate(user=coach.user)
        resp = self.client.get('/api/sessions/{}/individual_results/'
                               '?athletes=1'.format(session.pk),
                               format='json')
        self.assertEqual(resp.data['results'][0]['first_seen'], start_time)

    def test_individual_results_first_seen_none(self):
        """Test first seen with no splits and no start button."""
        coach = Coach.objects.get(user__username='alsal')
        session = TimingSession.objects.create(coach=coach, name='test')
        self.client.force_authenticate(user=coach.user)
        resp = self.client.get('/api/sessions/{}/individual_results/'
                               '?athletes=1'.format(session.pk),
                               format='json')
        self.assertIsNone(resp.data['results'][0]['first_seen'])

    def test_roster_upload_with_tags(self):
        """Test uploading a roster with tag and bib information."""
        user = User.objects.get(username='alsal')
        session = TimingSession.objects.create(
            name='upload', coach=Coach.objects.get(user=user))
        self.client.force_authenticate(user=user)
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='r+w') \
                as _roster:
            _roster.write(
                'first_name,last_name,birth_date,rfid_code,bib_number\n'
                'Ryan,Hall,,0000 0001,101')
            _roster.seek(0)
            resp = self.client.post(
                '/api/sessions/{}/upload_runners/'.format(session.pk),
                data={'file': [_roster]})
            self.assertEqual(resp.status_code, 204)
        self.assertTrue(Team.objects.filter(
            name='session-{}-default-team'.format(session.pk)).exists())
        self.assertTrue(Tag.objects.filter(
            bib='101', id_str='0000 0001').exists())

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

    def test_post_splits_bulk_single_failure(self):
        """Test that a single bad split does not prevent other
        splits from being saved.
        """
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)

        # The second split is bad because it contains a
        # non-registered tag.
        resp = self.client.post('/api/splits/',
            data=json.dumps([
                {'reader': 'A1010',
                 'athlete': None,
                 'time': 1234,
                 'tag': 'AAAA 0001',
                 'sessions': []},
                {'reader': 'A1010',
                 'athlete': None,
                 'time': 1235,
                 'tag': 'notatag123',
                 'sessions': []},
            ]),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        new_split_1 = Split.objects.filter(time=1234, athlete=1,
                                           reader__id_str='A1010')
        self.assertTrue(new_split_1.exists())

    def test_timestamp_conversion(self):
        """Test that datetimes are converted to timestamps."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/splits/',
            data=json.dumps({
                'reader': 'A1010',
                'athlete': 1,
                'time': '2015/01/01 01:01:01.123',
                'tag': None,
                'sessions': []}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['time'], 1420074061123)

    def test_split_add_session(self):
        """Test that a split is added to the given session(s)."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        with mock.patch.object(TimingSession, 'clear_cache') as mock_clear:
            resp = self.client.post('/api/splits/',
                data=json.dumps({
                    'reader': None,
                    'athlete': 1,
                    'time': '2015/01/01 01:01:01.123',
                    'tag': None,
                    'sessions': [1, 2]}),
                content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        split = Split.objects.get(pk=resp.data['id'])
        self.assertEqual(
            list(split.timingsession_set.values_list('id', flat=True)),
            [1, 2])

        # Make sure the cache was cleared for both sessions for this
        # athlete.
        mock_clear.assert_has_calls([mock.call(1), mock.call(1)])

    def test_anon_view_public_splits(self):
        """Test that anyone can view splits from public sessions."""
        public_splits = Split.objects.filter(timingsession__private=False)
        resp = self.client.get('/api/splits/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([split['id'] for split in resp.data],
                         list(public_splits.values_list('id', flat=True)))

    def test_auth_view_splits(self):
        """Test that a coach can access splits that are in his sessions."""
        coach = Coach.objects.get(user__username='alsal')
        coach_splits = Split.objects.filter(timingsession__coach=coach)
        self.client.force_authenticate(user=coach.user)
        resp = self.client.get('/api/splits/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([split['id'] for split in resp.data],
                         list(coach_splits.values_list('id', flat=True)))

    def test_filter_splits_checkpoint(self):
        """Test filtering splits by checkpoint."""
        session = TimingSession.objects.get(pk=1)
        reader = Reader.objects.create(id_str='Z1010', coach=session.coach)
        session.readers.add(reader)
        athlete = Athlete.objects.first()
        checkpoint = Checkpoint.objects.create(session=session,
                                                name='CP1')
        checkpoint.readers.add(reader)
        split = Split.objects.create(reader=reader, athlete=athlete,
                                     time=11000)
        SplitFilter.objects.create(timingsession=session, split=split)
        resp = self.client.get(
            '/api/splits/?checkpoint={}'.format(checkpoint.pk), format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], split.pk)


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

    fixtures = ['trac_min.json']

    def setUp(self):
        self.user_data = {
            'username': 'newuser',
            'password': 'password',
            'email': 'email@gmail.com',
            'user_type': None
        }

    def test_register_athlete(self):
        """Test registering an athlete."""
        self.user_data['user_type'] = 'athlete'
        resp = self.client.post('/api/register/',
                                data=json.dumps(self.user_data),
                                content_type='application/json')
        self.assertTrue(Athlete.objects.get(user__username="newuser"))
        self.assertEqual(resp.status_code, 201)

    def test_register_coach(self):
        """Test registering a coach."""
        self.user_data['user_type'] = 'coach'
        resp = self.client.post('/api/register/',
                                data=json.dumps(self.user_data),
                                content_type='application/json')
        self.assertTrue(Coach.objects.get(user__username="newuser"))
        self.assertEqual(resp.status_code, 201)

    def test_register_coach_team(self):
        """Test creating a team when the coach is created."""
        self.user_data['user_type'] = 'coach'
        self.user_data['organization'] = 'My Team'
        resp = self.client.post('/api/register/',
                                data=json.dumps(self.user_data),
                                content_type='application/json')
        self.assertTrue(Coach.objects.get(user__username="newuser"))
        self.assertEqual(resp.status_code, 201)
        # The team that the coach signs up with should be designated
        # as his primary team.
        self.assertTrue(Team.objects.filter(coach__user__username='newuser',
                                            name='My Team').exists())

    def test_login(self):
        """Test fetching an access token."""
        resp = self.client.post(
            '/api/login/',
            {'username': 'alsal',
             'password': 'password',
             'grant_type': 'password',
             'client_id': 'aHD4NUa4IRjA1OrPD2kJLXyz34c06Bi5eVX8O94p'},
            format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['user']['username'], 'alsal')
        self.assertEqual(resp.data['user']['user_type'], 'coach')

    def test_verify_login(self):
        """Test validating an access token."""
        application = Application.objects.get(pk=1)
        AccessToken.objects.create(
            token='1234',
            expires=(timezone.now() + timezone.timedelta(days=1)),
            application=application)
        AccessToken.objects.create(
            token='5678',
            expires=(timezone.now() - timezone.timedelta(days=1)),
            application=application)
        resp = self.client.get('/api/verifyLogin/', {'token': '1234'})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/verifyLogin/', {'token': '5678'})
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/api/verifyLogin/', {'token': '2112'})
        self.assertEqual(resp.status_code, 404)


class RockBlockTestCase(APITestCase):

    def test_rockblock_receive(self):
        """Test receiving a message from a rock block."""
        resp = self.client.post('/api/rockblock/',
                                {'imei': 300234010753370,
                                 'momsn': 12345,
                                 'transmit_time': '12-10-10 10:41:50',
                                 'iridium_latitude': 52.3867,
                                 'iridium_longitude': 0.2938,
                                 'iridium_cep': 8,
                                 'data': 'hello world'.encode('hex')})
        self.assertEqual(resp.status_code, 200)


class CheckpointViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            '/api/sessions/1/checkpoints/',
            data=json.dumps({'name': 'A', 'readers': ['A1010']}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Checkpoint.objects.filter(
            readers__id_str='A1010', session=1).exists())

    def test_update_checkpoint(self):
        """Test updating an existing checkpoint."""
        reader = Reader.objects.get(id_str='A1010')
        session = TimingSession.objects.get(pk=1)
        checkpoint = Checkpoint.objects.create(session=session,
                                               name='CP1')
        checkpoint.readers.add(reader)
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.patch(
            '/api/sessions/1/checkpoints/{}/'.format(checkpoint.pk),
            data=json.dumps({'name': 'CP2'}),
            content_type='application/json')
        self.assertEqual(resp.data['id'], checkpoint.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Checkpoint.objects.filter(
            readers__id_str='A1010', session=1, name='CP2').exists())

    def test_filter_checkpoint_reader(self):
        """Test filtering checkpoints by reader."""
        reader = Reader.objects.get(id_str='A1010')
        session = TimingSession.objects.get(pk=1)
        checkpoint1 = Checkpoint.objects.create(session=session,
                                                name='CP1')
        checkpoint1.readers.add(reader)
        checkpoint2 = Checkpoint.objects.create(session=session,
                                                name='CP2')
        resp = self.client.get('/api/sessions/1/checkpoints/?reader=A1010',
                               format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], checkpoint1.pk)
