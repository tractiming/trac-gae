from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
import mock
from trac.models import User, TimingSession
#import trac.models
from api.views import *
from rest_framework.test import APITestCase
from provider.oauth2.models import Client, AccessToken
from rest_framework.test import APIRequestFactory, force_authenticate



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
    
    def test_get_tags_athlete(self):
        """Test an athlete can only view his tags."""
        user = User.objects.get(username='grupp')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/tags/', format='json')
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], 1)


class AthleteViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    def test_get_athletes_coach(self):
        """Test that a coach can view all his athletes."""
        pass

    def test_get_athletes_athlete(self):
        """Test an athlete can only view himself."""
        pass

    def test_pre_save(self):
        """Test that a user is created before the athlete is."""
        pass


class TimingSessionViewSetTest(APITestCase):

    fixtures = ['trac_min.json']

    @mock.patch('trac.models.TimingSession')
    def test_individual_results(self, mock_session):
        user = User.objects.get(username='alsal')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/sessions/1/individual_results/', format='json')
        #mock_session.objects.get.assert_called_with(pk=1)



