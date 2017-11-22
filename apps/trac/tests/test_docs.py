from django.contrib.auth.models import User
from rest_framework.test import APITestCase, force_authenticate


class SwaggerDocsTest(APITestCase):

    def test_generate_docs(self):
        """Test that there are no errors when generating docs."""
        user = User.objects.create(username='docuser', is_superuser=True)
        self.client.force_authenticate(user=user)
        resp = self.client.get('/docs/api-docs/api')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/docs/api-docs/stats')
        self.assertEqual(resp.status_code, 200)
