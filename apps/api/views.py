from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import link
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from provider.oauth2.models import Client

from permissions import IsManagerOrReadOnly
from serializers import UserSerializer, RegistrationSerializer
from serializers import TagSerializer, TimingSessionSerializer

from trac.models import TimingSession


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = renderers.JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RegistrationView(APIView):
    """
    Registers a user and creates server-side client.

    Parameters: username, password
    """
    permission_classes = ()

    def post(self, request):
        serializer = RegistrationSerializer(data=request.DATA)

        if not serializer.is_valid():
            return HttpResponse(serializer.errors,
                    status=status.HTTP_404_BAD_REQUEST)
        data = serializer.data

        # Create the user in the database.
        u = User.objects.create(username=data['username'])
        u.set_password(data['password'])
        u.save()

        # Create the OAuth2 client.
        name = u.username
        client = Client(user=u, name=name, url=''+name,
                client_id=name, client_secret='', client_type=1)
        client.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ModelViewSet):
    """
    Returns a list of tags associated with the current user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        tags = Tag.objects.filter(user=user)
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class CompletedSessionsView(viewsets.ReadOnlyModelViewSet):
    """
    Returns a list of sessions completed (run) by the current user.
    
    NOT IMPLEMENTED
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TimingSessionSerializer

    def get_queryset(self):
        """
        Overrides default method to filter sessions by user.
        """
        user = self.request.user
        return TimingSession.objects.all()


class ManagedSessionsView(viewsets.ModelViewSet):
    """
    Returns a list of sessions managed (coached) by the current user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TimingSessionSerializer

    def get_queryset(self):
        """
        Overrides default method to filter sessions by user.
        """
        user = self.request.user
        return TimingSession.objects.filter(manager=user)


class TimingSessionViewSet(viewsets.ModelViewSet):
    queryset = TimingSession.objects.all()
    serializer_class = TimingSessionSerializer
    permission_classes = (IsAuthenticated,)

    @link(renderer_classes=(renderers.JSONRenderer,))
    def results(self, request, *args, **kwargs):
        session = self.get_object()
        result_set = {'wid': session.id,}
        return JSONResponse(result_set)
    
    #def pre_save(self, obj):
    #    obj.owner = self.request.user
    
