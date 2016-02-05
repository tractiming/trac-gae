import datetime

import mock
from django.test import TestCase
from django.utils import timezone

import trac.models
from trac.models import (
    Athlete, Coach, User, Reader, TimingSession, Split, Tag
)

class ReaderTestCase(TestCase):

    fixtures = ['trac_min.json']

    def test_active_sessions(self):
        """Test finding active/inactive sessions."""
        start = timezone.now()
        inactive_stop = timezone.now()+timezone.timedelta(-1)
        active_stop = timezone.now()+timezone.timedelta(1)
        session = TimingSession.objects.get(pk=1)
        reader = Reader.objects.get(pk=1)
        session.start_time = start
        session.stop_time = inactive_stop
        session.save()
        self.assertNotIn(session, reader.active_sessions)
        session.stop_time = active_stop
        session.save()
        self.assertIn(session, reader.active_sessions)


class AthleteTestCase(TestCase):

    fixtures = ['trac_min.json']

    @mock.patch.object(trac.models, 'datetime')
    def test_age(self, mock_datetime):
        """Test calculating an athlete's age."""
        galen = Athlete.objects.get(user__username='grupp')
        cam = Athlete.objects.get(user__username='clevins')
        mock_datetime.date.today.return_value = datetime.date(2000, 5, 27)
        self.assertIsNone(galen.age())
        self.assertEqual(cam.age(), 10)

    def test_age_as_of_date(self):
        """Test calculating age on a certain date."""
        cam = Athlete.objects.get(user__username='clevins')
        age = cam.age(as_of_date=datetime.date(2000, 5, 27))
        self.assertEqual(age, 10)

    def test_delete_user(self):
        """Test that the user is deleted after the athlete."""
        user = User.objects.create(username='testuser')
        athlete = Athlete.objects.create(user=user)
        athlete.delete()
        self.assertFalse(User.objects.filter(username='testuser').exists())


class CoachTestCase(TestCase):

    def test_delete_user(self):
        """Test that the user is deleted after the coach."""
        user = User.objects.create(username='testuser')
        coach = Coach.objects.create(user=user)
        coach.delete()
        self.assertFalse(User.objects.filter(username='testuser').exists())


class TimingSessionTestCase(TestCase):

    fixtures = ['trac_min.json', 'teams.json']

    def setUp(self):
        self.session = TimingSession.objects.get(pk=1)

    def test_num_athletes(self):
        """Test finding number of athletes in the session."""
        self.assertEqual(self.session.num_athletes, 2)

    def test_sorted_athletes(self):
        """Test sorting athletes by time."""
        self.assertListEqual(
            list(self.session._sorted_athlete_list(10, 0)), [2, 1])
        self.assertListEqual(
            list(self.session._sorted_athlete_list(1, 0)), [2])
        self.assertListEqual(
            list(self.session._sorted_athlete_list(10, 1)), [1])

    def test_sorted_athletes_without_start_button(self):
        """Test sorting times with no start button."""
        self.session.start_button_time = None
        self.session.save()
        self.assertListEqual(
            list(self.session._sorted_athlete_list(10, 0)), [2, 1])
        self.assertListEqual(
            list(self.session._sorted_athlete_list(1, 0)), [2])
        self.assertListEqual(
            list(self.session._sorted_athlete_list(10, 1)), [1])

    @mock.patch('trac.models.cache')
    def test_clear_results(self, mock_cache):
        """Test clearing the results from a session."""
        split = Split.objects.all()[0]
        session1 = TimingSession.objects.get(pk=1)
        session2 = TimingSession.objects.create(name='Second session',
                                                coach=Coach.objects.all()[0])
        session2.splits.add(split.pk)

        # Clear split from session one. Split still exists and belongs to
        # session two.
        session1.clear_results()
        self.assertEqual(session1.splits.all().count(), 0)
        self.assertEqual(session2.splits.all().count(), 1)
        self.assertEqual(
            Split.objects.all().count(),
            Split.objects.exclude(timingsession=1).count())
        mock_cache.delete.assert_any_call('ts_1_athlete_1_results')
        mock_cache.delete.assert_any_call('ts_1_athlete_2_results')

        # Clear the split from session two. It no longer belongs to any session
        # and should be deleted.
        session2.clear_results()
        self.assertEqual(
            Split.objects.filter(timingsession=session2.pk).count(), 0)
        mock_cache.delete.assert_called_with('ts_{}_athlete_1_results'.format(
            session2.id))

    def test_is_active(self):
        """Test determining if the workout is open or closed."""
        # Open the workout by advancing the stop time.
        self.session.start_time = timezone.now()
        self.session.stop_time = self.session.start_time+timezone.timedelta(days=1)
        self.session.save()
        self.assertTrue(self.session.active)

        # Close the workout by setting start time to stop time.
        self.session.stop_time = self.session.start_time
        self.session.save()
        self.assertFalse(self.session.active)

    @mock.patch('trac.models.cache')
    def test_athlete_splits(self, mock_cache):
        """Test calculating results for each athlete."""
        # Mock calls to the cache.
        mock_cache.get.return_value = None

        res_1 = self.session._calc_athlete_splits(1)
        mock_cache.get.assert_called_with('ts_1_athlete_1_results')
        mock_cache.set.assert_called_with('ts_1_athlete_1_results',
                (res_1.user_id, res_1.name, res_1.team, res_1.splits))
        self.assertListEqual(res_1.splits, [122.003, 197.237, 69.805])
        self.assertEqual(sum(res_1.splits), res_1.total)

        res_2 = self.session._calc_athlete_splits(2)
        mock_cache.get.assert_called_with('ts_1_athlete_2_results')
        mock_cache.set.assert_called_with('ts_1_athlete_2_results',
                (res_2.user_id, res_2.name, res_2.team, res_2.splits))
        self.assertListEqual(res_2.splits, [123.021, 195.58])
        self.assertEqual(sum(res_2.splits), res_2.total)

    def test_splits_with_filter(self):
        """Test calculating splits while ignoring some."""
        session = TimingSession.objects.get(pk=2)
        results = session.individual_results(apply_filter=True)
        # Check that last split gets filtered out.
        self.assertEqual(len(results[0].splits), 1)
        self.assertEqual(results[0].total, 389.047)

    def test_individual_results(self):
        """Test calculating individual results."""
        pass

    def test_individual_results_athlete_list(self):
        """Test calculating results given a list of athlete IDs."""
        session = TimingSession.objects.get(pk=1)
        results = session.individual_results(athlete_ids=[1, 1])
        self.assertEqual([1], [result.user_id for result in results])

    def test_team_results(self):
        """Test calculating team results."""
        session = TimingSession.objects.get(pk=101)
        results = session.team_results()
        scores = [(team['id'], team['score']) for team in results]
        self.assertEqual(scores, [(101, 30), (102, 42), (103, 52)])

    def test_archive(self):
        """Test results remain after tag is reassigned."""
        tag = Tag.objects.get(pk=1)
        user = User.objects.create(first_name='Mo', last_name='Farah',
                                   username='mo')
        athlete = Athlete.objects.create(user=user)
        tag.athlete = athlete
        tag.save()
        results = self.session.individual_results()
        self.assertEqual(results[1].name, 'Galen Rupp')

    def test_delete_session(self):
        """Test that splits are deleted with the session."""
        self.session.delete()
        self.assertEqual(Split.objects.all().count(),
                         Split.objects.exclude(timingsession=1).count())


