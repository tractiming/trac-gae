import datetime

import mock
from django.test import TestCase
from django.utils import timezone

import trac.models
from trac.models import (
    Athlete, Coach, User, Reader, TimingSession, Split, Tag, SplitFilter
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
        SplitFilter.objects.create(timingsession=session2, split=split)

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


class SplitFilterTestCase(TestCase):

    def setUp(self):
        user1 = User.objects.create(username='lpuskedra')
        user2 = User.objects.create(username='self')
        self.athlete = Athlete.objects.create(user=user1)
        self.session = TimingSession.objects.create(
            name='A', coach=Coach.objects.create(user=user2))
        self.split1 = Split.objects.create(time=0, athlete=self.athlete)
        self.split2 = Split.objects.create(time=12000, athlete=self.athlete)
        self.split3 = Split.objects.create(time=20000, athlete=self.athlete)

    def test_create_no_times(self):
        """Test that a split for an athlete with no time isn't filtered."""
        split = SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        self.assertTrue(self.session.splits.filter(
            splitfilter__filtered=False).exists())
        self.assertFalse(split.filtered)

    def test_create_filter(self):
        """Test correct filter is chosen based on time threshold."""
        split1 = SplitFilter.objects.create(timingsession=self.session,
                                            split=self.split1)
        split2 = SplitFilter.objects.create(timingsession=self.session,
                                            split=self.split2)
        split3 = SplitFilter.objects.create(timingsession=self.session,
                                            split=self.split3)
        self.assertFalse(split1.filtered)
        self.assertFalse(split2.filtered)
        self.assertTrue(split3.filtered)

    def test_create_start_button(self):
        """Test that filtering uses the start button if present."""
        self.session.start_button_time = 10000
        self.session.save()
        split = SplitFilter.objects.create(timingsession=self.session,
                                           split=self.split2)
        self.assertTrue(split.filtered)
