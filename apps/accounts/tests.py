import json

import mock
from django.contrib.auth.models import User
from oauth2_provider.models import Application
from rest_framework.test import APITestCase

from accounts import views
from accounts.models import GoogleSignIn


class GoogleSignInTest(APITestCase):

    fixtures = ['fixture.json']

    def test_existing_signin(self):
        """Test signing in an existing user."""
        user = User.objects.get(username='alsal')
        google_id = GoogleSignIn.objects.get(user=user).google_id
        with mock.patch.object(views, '_get_user_id') as mock_id:
            mock_id.return_value = google_id
            resp = self.client.post(
                '/google-auth/',
                data=json.dumps({
                    'id_token': 'mysecretidtoken',
                    'google_client_id': google_id,
                    'trac_client_id': Application.objects.get(pk=1).client_id,
                    'email': 'me@gmail.com'
                }),
                content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['user']['username'], 'alsal')
        mock_id.assert_called_once_with('mysecretidtoken', google_id)

    @mock.patch.object(views, 'uuid')
    def test_new_user_signin(self, mock_uuid):
        """Test registering a user using Google credentials."""
        google_id = '294039502957910482904'
        mock_uuid.uuid4().hex = '42'
        with mock.patch.object(views, '_get_user_id') as mock_id:
            mock_id.return_value = google_id
            resp = self.client.post(
                '/google-auth/',
                data=json.dumps({
                    'id_token': 'mysecretidtoken',
                    'google_client_id': google_id,
                    'trac_client_id': Application.objects.get(pk=1).client_id,
                    'email': 'me@gmail.com'
                }),
                content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['user']['username'], '42')
        self.assertEqual(resp.data['user']['email'], 'me@gmail.com')
        self.assertEqual(resp.data['user']['user_type'], 'coach')
        mock_id.assert_called_once_with('mysecretidtoken', google_id)

    def test_link_existing_user(self):
        """Test linking a Google account to a trac account."""
        user = User.objects.create(username='agoucher')
        self.client.force_authenticate(user=user)
        google_id = '194850798290424876193'
        with mock.patch.object(views, '_get_user_id') as mock_id:
            mock_id.return_value = google_id
            resp = self.client.post(
                '/google-auth/',
                data=json.dumps({
                    'id_token': 'mysecretidtoken',
                    'google_client_id': google_id,
                    'trac_client_id': Application.objects.get(pk=1).client_id,
                    'email': 'me@gmail.com'
                }),
                content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['user']['username'], 'agoucher')
        self.assertTrue(GoogleSignIn.objects.filter(
            user=user, google_id=google_id).exists())
        mock_id.assert_called_once_with('mysecretidtoken', google_id)

    def test_bad_idtoken(self):
        """Test that we return a 400 if `id_token` is invalid."""
        with mock.patch.object(views, '_get_user_id') as mock_id:
            mock_id.return_value = None
            resp = self.client.post(
                '/google-auth/',
                data=json.dumps({
                    'id_token': 'badtoken',
                    'google_client_id': 'googleid',
                    'trac_client_id': 'clientid',
                    'email': 'me@gmail.com'
                }),
                content_type='application/json')
        self.assertEqual(resp.status_code, 400)
