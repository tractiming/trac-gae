from django.test import TestCase

from trac.models import Athlete, Coach, User
from trac.utils.filter_util import get_filter_constant
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

