from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import (link, api_view, permission_classes,
detail_route)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from provider.oauth2.models import Client

from permissions import IsOwner, IsManager, IsCoachOf
from serializers import UserSerializer, RegistrationSerializer
from serializers import TagSerializer, TimingSessionSerializer
from serializers import ReaderSerializer
from serializers import AthleteProfileSerializer

import datetime

from trac.models import TimingSession, AthleteProfile, CoachProfile
from trac.models import Tag, Reader, TagTime
from trac.util import is_athlete, is_coach


class JSONResponse(HttpResponse):
    """
    Renders contents to JSON.
    """
    def __init__(self, data, **kwargs):
        content = renderers.JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

class RegistrationView(APIView):
    """
    Registers a user and creates server-side client.
    """
    permission_classes = ()

    def post(self, request):
        serializer = RegistrationSerializer(data=request.DATA)

        if not serializer.is_valid():
            print 'bad serializer'
            return HttpResponse(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data

        # Create the user in the database.
        user = User.objects.create(username=data['username'])
        user.set_password(data['password'])
        user.save()
            
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

        # Create the OAuth2 client.
        name = user.username
        client = Client(user=user, name=name, url=''+name,
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
        return tags

    def pre_save(self, obj):
        obj.user = self.request.user


class AthleteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsCoachOf, )
    serializer_class = AthleteProfileSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            cp = CoachProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            return []

        return cp.athletes.all()

    def pre_save(self, obj):
        if is_coach(self.request.user):
            cp = CoachProfile.objects.get(user=self.request.user)
            obj.coachprofile_set.append(cp.pk)

class ReaderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwner, )
    serializer_class = ReaderSerializer

    def get_queryset(self):
        user = self.request.user
        readers = Reader.objects.filter(owner=user)
        return readers

    def pre_save(self, obj):
        obj.owner = self.request.user


class TimingSessionViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all sessions associated with the user.
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (IsManager,)


    def get_queryset(self):
        """
        Overrides default method to filter sessions by user.
        """
        user = self.request.user

        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            ap = AthleteProfile.objects.get(user=user)
            sessions = ap.get_completed_sessions()

        elif is_coach(user):
            sessions = TimingSession.objects.filter(manager=user)

        # If not a user or coach, no results can be found.
        else:
            sessions = []

        return sessions    

    def pre_save(self, obj):
        """Assigns a manager to the workout before it is saved."""
        obj.manager = self.request.user

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def post_splits(request):
    """Receives updates from readers."""
    data = request.POST
    #print data
    return HttpResponse(status.HTTP_200_OK)
    
    # Get the tag and reader associated with the notification. Note that if the
    # tag or reader has not been established in the system, the split will be
    # ignored here.
    '''
    try:
        reader = Reader.objects.get(id_str=data['r'])
        tag = Tag.objects.get(id_str=data['id'])
    except ObjectDoesNotExist:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)
    
    # Create new TagTime.
    dtime = datetime.datetime.strptime(data['time'], "%Y/%m/%d %H:%M:%S.%f") 
    tt = TagTime(tag_id=tag.id, time=dtime, reader_id=reader.id)
    try:
        tt.save()
    except IntegrityError:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)

    # Add the TagTime to all sessions active and having a related reader.
    for s in reader.active_sessions:
        s.tagtimes.add(tt.pk)
    
    return HttpResponse(status.HTTP_201_CREATED)
    '''

@api_view(['GET'])
@permission_classes((AllowAny,))
def verify_login(request):
    """
    Checks if the user is logged in. Returns a JSON response.
    """
    print request.user
    return HttpResponse()
