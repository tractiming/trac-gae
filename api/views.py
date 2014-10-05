from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import permissions

from permissions import IsManagerOrReadOnly
from serializers import UserSerializer, TimingSessionSerializer

from common.models import TimingSession

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class TimingSessionViewSet(viewsets.ModelViewSet):
    queryset = TimingSession.objects.all()
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
            IsManagerOrReadOnly,)

    #def results(self, request, *args, **kwargs):
    #    session = self.get_object()
    #    return session
    #def pre_save(self, obj):
    #    obj.owner = self.request.user
    
