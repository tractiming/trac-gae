from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
import mock
from trac.models import *
from api.views import *
from rest_framework.test import APITestCase
from provider.oauth2.models import Client, AccessToken
from rest_framework.test import APIRequestFactory, force_authenticate



class TagViewSetTestCase(APITestCase):

    fixtures = ['trac_min.json']


    def test_get_queryset(self):
        #url = reverse('api/tags')
        #self.client.force_authenticate(user=User.objects.get(username='alsal'))
        #resp = self.client.get('/tags/1')
        #resp = TagViewSet(self.client)
        #print resp.data
        print(Tag.objects.all())
        factory = APIRequestFactory()
        request = factory.get('/api/tags', '', content_type='application/json')
        user = User.objects.get(username='alsal')
        view = TagViewSet.as_view(actions={'get': 'retrieve'})
        #self.client.force_authenticate(user=user)
        #resp = self.client.get('/api/tags/1/', format='json')
        #print(resp)
        #import pdb; pdb.set_trace()
        #request = factory.get('/api/tags/')
        #force_authenticate(request, user=user)
        print user.is_authenticated
        request.user = user
        response = view(request)
        print response.data


    def test_something(self):
        pass
