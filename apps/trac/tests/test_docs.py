from django.contrib.auth.models import User
from rest_framework.test import APITestCase, force_authenticate


class SwaggerDocsTest(APITestCase):

    def test_generate_docs(self):
        """Test that there are no errors when generating docs."""
        user = User.objects.create(username='docuser')
        user.is_superuser=True
        user.set_password('password')
        user.save()
        import ipdb; ipdb.set_trace()
        self.client.force_authenticate(user=user)
        resp = self.client.get('/docs/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/docs/api-docs/api')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/docs/api-docs/stats')
        self.assertEqual(resp.status_code, 200)
