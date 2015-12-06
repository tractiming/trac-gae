from django.test import TestCase, Client
from django.contrib.auth.models import User


class SwaggerDocsTest(TestCase):

    def test_generate_docs(self):
        """Test that there are no errors when generating docs."""
        user = User.objects.create(username='docuser')
        user.is_superuser = True # docs are for superusers only
        user.set_password('password')
        user.save()
        client = Client()
        client.login(username='docuser', password='password')
        resp = client.get('/docs/')
        self.assertEqual(resp.status_code, 200)
        resp = client.get('/docs/api-docs/api')
        self.assertEqual(resp.status_code, 200)
        resp = client.get('/docs/api-docs/stats')
        self.assertEqual(resp.status_code, 200)
