import datetime

import mock
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

import trac.models
from trac.models import (
    Athlete, Coach, User, Reader, TimingSession, Split, Tag, SplitFilter,
    Checkpoint
)
from trac.utils.split_util import format_total_seconds

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
                (res_1.user_id, res_1.name, res_1.team, res_1.splits,
                 res_1.total, res_1.first_seen))
        self.assertListEqual(res_1.splits, [122.003, 197.237, 69.805])
        self.assertEqual(sum(res_1.splits), res_1.total)

        res_2 = self.session._calc_athlete_splits(2)
        mock_cache.get.assert_called_with('ts_1_athlete_2_results')
        mock_cache.set.assert_called_with('ts_1_athlete_2_results',
                (res_2.user_id, res_2.name, res_2.team, res_2.splits,
                 res_2.total, res_2.first_seen))
        self.assertListEqual(res_2.splits, [123.021, 195.58])
        self.assertEqual(sum(res_2.splits), res_2.total)

    def test_splits_with_filter(self):
        """Test calculating splits while ignoring some."""
        session = TimingSession.objects.get(pk=2)
        session.refresh_split_filters()
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

    def test_overwrite_final_time(self):
        """Test overwriting an athlete's final time."""
        session = TimingSession.objects.create(coach=self.session.coach,
                                               name='test')
        athlete = Athlete.objects.first()
        session._overwrite_final_time(athlete.id, 1, 2, 3, 456)
        results = session.individual_results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].total,
                         (1*3600000 + 2*60000 + 3*1000 + 456)/1000.0)

    def test_delete_splits(self):
        """Test deleting splits from an athlete's results."""
        athlete = Athlete.objects.get(user__username='clevins')
        self.session._delete_split(athlete.pk, 0)
        results = self.session.individual_results()
        self.assertEqual(results[0].splits, [195.58])


class SplitTestCase(TestCase):

    def setUp(self):
        coach = Coach.objects.create(
            user=User.objects.create(username='cquick'))
        self.session = TimingSession.objects.create(name='test pace',
                                                    coach=coach)
        athlete = Athlete.objects.create(
            user=User.objects.create(username='sagarpatel'))
        self.reader1 = Reader.objects.create(id_str='Z2111', name='reader 1',
                                             coach=coach)
        self.reader2 = Reader.objects.create(id_str='Z2112', name='reader 2',
                                             coach=coach)
        self.split1 = Split.objects.create(athlete=athlete, time=300000,
                                           reader=self.reader1)
        self.split2 = Split.objects.create(athlete=athlete, time=600000,
                                           reader=self.reader2)

    def test_calc_pace_multiple_checkpoints(self):
        """Test calculating pace in a session with multiple checkpoints."""
        checkpoint1 = Checkpoint.objects.create(session=self.session,
                                                name='A', distance=1)
        checkpoint2 = Checkpoint.objects.create(session=self.session,
                                                name='B', distance=2)
        checkpoint1.readers.add(self.reader1)
        checkpoint2.readers.add(self.reader2)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split2)

        pace = self.split2.calc_pace(self.session)
        self.assertEqual(pace, '{} min/miles'.format(format_total_seconds(5)))

    def test_calc_pace_one_checkpoint_with_start(self):
        """Test calculating pace with a start and one checkpoint."""
        self.session.start_button_time = 0
        self.session.save()
        checkpoint1 = Checkpoint.objects.create(session=self.session,
                                                name='A', distance=1)
        checkpoint1.readers.add(self.reader1)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        pace = self.split1.calc_pace(self.session)
        self.assertEqual(pace, '{} min/miles'.format(format_total_seconds(5)))

    def test_calc_pace_one_checkpoint_no_start(self):
        """Test that pace is none with a single checkpoint and no start."""
        checkpoint1 = Checkpoint.objects.create(session=self.session,
                                                name='A', distance=1)
        checkpoint1.readers.add(self.reader1)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        pace = self.split1.calc_pace(self.session)
        self.assertIsNone(pace)

    def test_calc_pace_checkpoint_no_distance(self):
        """Test that pace is not calculated if no checkpoint distance."""
        checkpoint1 = Checkpoint.objects.create(session=self.session, name='A')
        checkpoint1.readers.add(self.reader1)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        pace = self.split1.calc_pace(self.session)
        self.assertIsNone(pace)

    def test_calc_pace_unit_conversion(self):
        """Test calculating pace with a unit conversion."""
        checkpoint1 = Checkpoint.objects.create(
            session=self.session, name='A', distance=1609.34,
            distance_units='m')
        checkpoint2 = Checkpoint.objects.create(
            session=self.session, name='B', distance=3218.64,
            distance_units='m')
        checkpoint1.readers.add(self.reader1)
        checkpoint2.readers.add(self.reader2)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split1)
        SplitFilter.objects.create(timingsession=self.session,
                                   split=self.split2)

        pace = self.split2.calc_pace(self.session)
        self.assertEqual(pace, '{} min/miles'.format(format_total_seconds(5)))


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

    def test_max_num_splits_filter(self):
        """Test filtering based on a maximum number of splits."""
        self.session.filter_max_num_splits = 1
        self.session.save()
        split1 = SplitFilter.objects.create(timingsession=self.session,
                                            split=self.split1)
        split2 = SplitFilter.objects.create(timingsession=self.session,
                                            split=self.split2)
        self.assertFalse(split1.filtered)
        self.assertTrue(split2.filtered)


class CheckpointTestCase(TestCase):

    fixtures = ['trac_min.json']

    def test_unique_readers_session(self):
        """Check that one reader can't be added to more than one checkpoint
        in the same session.
        """
        coach = Coach.objects.get(user__username='alsal')
        session = TimingSession.objects.first()
        reader = Reader.objects.create(coach=coach, name='1')
        checkpoint1 = Checkpoint.objects.create(session=session, name='A')
        checkpoint2 = Checkpoint.objects.create(session=session, name='B')

        checkpoint1.readers.add(reader)
        with self.assertRaises(IntegrityError):
            checkpoint2.readers.add(reader)
