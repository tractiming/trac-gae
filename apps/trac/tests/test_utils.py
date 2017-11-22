from django.test import TestCase

from trac.models import Athlete, Coach, User, TimingSession

from trac.utils.filter_util import get_filter_constant
from trac.utils.integrations import format_tfrrs_results
from trac.utils.split_util import convert_units
from trac.utils.user_util import is_athlete, is_coach, user_type


class UtilsTestCase(TestCase):

    fixtures = ['trac_min.json']

    def test_is_athlete(self):
        """Test identifying an athlete."""
        athlete = Athlete.objects.all()[0]
        coach = Coach.objects.all()[0]
        self.assertFalse(is_athlete(coach.user))
        self.assertTrue(is_athlete(athlete.user))

    def test_is_coach(self):
        """Test identifying a coach."""
        athlete = Athlete.objects.all()[0]
        coach = Coach.objects.all()[0]
        self.assertTrue(is_coach(coach.user))
        self.assertFalse(is_coach(athlete.user))

    def test_user_type(self):
        """Test classifying a user."""
        athlete = Athlete.objects.all()[0]
        coach = Coach.objects.all()[0]
        user = User.objects.create(username='fakeuser')
        self.assertEqual(user_type(coach.user), 'coach')
        self.assertEqual(user_type(athlete.user), 'athlete')
        self.assertEqual(user_type(user), 'user')

    def test_get_filter_constant(self):
        """Test getting a filter constant from track size/interval."""
        filters = [
            (200, 400, 20),
            (1200, 400, 55),
            (400, 200, 25)
        ]
        for interval, size, constant in filters:
            self.assertEqual(get_filter_constant(interval, size), constant)

    def test_convert_distance_units(self):
        """Test converting units of distance."""
        benchmarks = [
            ((2, 'miles', 'meters'), 3218.68),
            ((13.1, 'miles', 'kilometers'), 21.08241),
            ((8, 'kilometers', 'miles'), 4.97097),
            ((1500, 'meters', 'kilometers'), 1.5)
        ]
        for input_, output in benchmarks:
            self.assertAlmostEqual(convert_units(*input_), output, 2)

        with self.assertRaises(ValueError):
            convert_units(26.2, 'miles', 'parsecs')


class IntegrationsTestCase(TestCase):

    fixtures = ['trac_min.json']

    def test_tfrrs(self):
        """Test formatting tfrss results."""
        session = TimingSession.objects.get(pk=1)
        tfrrs_results = format_tfrrs_results(session)
        self.assertEqual(
            [','.join(result.values()) for result in tfrrs_results], 
            ['AAAA 0002,,Nike,,Cam,Levins,M,,1990-05-26,400,60 x '
             '400m,,,,,318.601,1,0,1,1,,,,,,',
             'AAAA 0001,,Nike,,Galen,Rupp,,,,400,60 x '
             '400m,,,,,389.045,1,0,2,2,,,,,,'])
