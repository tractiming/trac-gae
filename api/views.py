from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.decorators import link

from permissions import IsManagerOrReadOnly
from serializers import UserSerializer, TimingSessionSerializer

from common.models import TimingSession

class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = renderers.JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class TimingSessionViewSet(viewsets.ModelViewSet):
    queryset = TimingSession.objects.all()
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
            IsManagerOrReadOnly,)

    @link(renderer_classes=(renderers.JSONRenderer,))
    def results(self, request, *args, **kwargs):
        session = self.get_object()
        result_set = {'wid': session.id,}
        return JSONResponse(result_set)
    
    #def pre_save(self, obj):
    #    obj.owner = self.request.user
    
