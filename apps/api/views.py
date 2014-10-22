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
from serializers import ReaderSerializer

from trac.models import TimingSession, AthleteProfile, CoachProfile
from trac.util import is_athlete, is_coach


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
                    status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data
        print data

        # Create the user in the database.
        user = User.objects.create(username=data['username'])
        user.set_password(data['password'])
        user.save()
        print 'user created'
            
        user_type = data['user_type']
        if user_type == 'athlete':
            # Register an athlete.
            athlete = AthleteProfile()
            athlete.user = user
            athlete.save()

        elif user_type == 'coach':
            # Register a coach.
            coach = CoachProfile()
            coach.user = user
            coach.save()
        print 'created profile'

        # Create the OAuth2 client.
        name = user.username
        client = Client(user=user, name=name, url=''+name,
                client_id=name, client_secret='', client_type=1)
        client.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CreateWorkoutView(APIView):
    """
    Creates a timing session, e.g., a workout or race.
    """
    permission_classes = ()

    def post(self, request):
        serializer = CreateTimingSessionSerializer(data=request.DATA)

        if not serializer.is_valid():
            return HttpResponse(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data

        # Create the session in the database.
        session = TimingSession.create()
        session.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ModelViewSet):
    """
    Returns a list of tags associated with the current user.
    """
    #permission_classes = (,)#IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        tags = Tag.objects.filter(user=user)
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

class ReaderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = ReaderSerializer

    def get_queryset(self):
        user = self.request.user
        readers = Reader.objects.filter(owner=user)
        serializer = ReaderSerializer(readers, many=True)
        return Response(serializer.data)


class TimingSessionViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all sessions associated with the user.
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (IsAuthenticated,)


    def get_queryset(self):
        """
        Overrides default method to filter sessions by user.
        """
        user = self.request.user

        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            sessions = [] #FIXME

        elif is_coach(user):
            sessions = TimingSession.objects.filter(manager=user)

        # If not a user or coach, no results can be found.
        else:
            sessions = []

        return sessions    

    @link(renderer_classes=(renderers.JSONRenderer,))
    def results(self, request, *args, **kwargs):
        session = self.get_object()
        result_set = {'wid': session.id,}
        return JSONResponse(result_set)
    
