import datetime

from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils import timezone

from rest_framework import (viewsets, permissions, renderers, 
                            status, serializers, views)
from rest_framework.response import Response
from rest_framework.decorators import (link, api_view, permission_classes,
detail_route)
from rest_framework.parsers import MultiPartParser, FormParser

from provider.oauth2.models import Client, AccessToken

from serializers import (UserSerializer, RegistrationSerializer, 
                         TagSerializer, TimingSessionSerializer,
                         ReaderSerializer, UserSerializer, CSVSerializer)

from trac.models import TimingSession, AthleteProfile, CoachProfile
from trac.models import Tag, Reader, TagTime
from trac.util import is_athlete, is_coach
from django.http import Http404
from django.core.cache import cache

import ast

class JSONResponse(HttpResponse):
    """
    Renders contents to JSON.
    """
    def __init__(self, data, **kwargs):
        content = renderers.JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

class verifyLogin(views.APIView):
	permission_classes = ()
	def post(self,request):
		data = request.POST
		# print data
		#Does the token exist?
		try:
			token = AccessToken.objects.get(token=data['token'])
		except: #ObjectDoesNotExist:
			return Http404
		
		#Is the Token Valid?
		
		if token.expires < timezone.now():
			return Http404
		else:
			return HttpResponse(status.HTTP_200_OK)

class userType(views.APIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self,request):
		data = request.GET
		#Is the user in the coaches table?
		user = self.request.user
		try:
			cp = CoachProfile.objects.get(user=user)
		except: #NotCoach:
			try:
				ap = AthleteProfile.objects.get(user=user)
			except: #NotAthlete
				return HttpResponse(status.HTTP_404_NOT_FOUND)
			return HttpResponse("athlete")
		return HttpResponse("coach")


class RegistrationView(views.APIView):
    """
    Registers a user and creates server-side client.
    """
    permission_classes = ()

    def post(self, request):
        serializer = RegistrationSerializer(data=request.DATA)

        if not serializer.is_valid():
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
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):

        user = self.request.user

        # If the user is an athlete, display the tags he owns.
        if is_athlete(user):
            tags = user.tag_set.all()

        # If the user is a coach, list the tags owned by any of his athletes.
        elif is_coach(user):
            tags = []
            for athlete in user.coach.athletes.all():
                tags.extend(athlete.user.tag_set.all())
        
        return tags

    def create(self, request, *args, **kwargs):
        if is_athlete(self.request.user):
            request.DATA[u'user'] = self.request.user.pk
        return super(TagViewSet, self).create(request, *args, **kwargs)


class AthleteViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    # Note that we are using the user serializer to make it easier to create
    # both the user and the athlete at the same time.
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Overrides the default method to return the users that are associated
        with an athlete belonging to this coach.
        """
        user = self.request.user
        try:
            cp = CoachProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            return []

        return [a.user for a in cp.athletes.all()]
    
    def post_save(self, obj, **kwargs):
        """
        After the user object has been saved, we create an athlete and add him
        to the coach's roster.
        """
        athlete = AthleteProfile()
        athlete.user = obj
        athlete.save()

        if is_coach(self.request.user):
            cp = CoachProfile.objects.get(user=self.request.user)
            cp.athletes.add(athlete.pk)

class ReaderViewSet(viewsets.ModelViewSet):
    """
    The set of readers the coach owns.
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ReaderSerializer

    def get_queryset(self):
        user = self.request.user
        readers = Reader.objects.filter(owner=user)
        return readers

    def pre_save(self, obj):
        obj.owner = self.request.user

class IndividualTimes(views.APIView):
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, format=None):
        
        user = self.request.user
        # print user
        final_array = []
        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            ap = AthleteProfile.objects.get(user=user)
            sessions = ap.get_completed_sessions()
		#Iterate through each session
            for s in sessions:
			    primary_key = s.pk
			    t = TimingSession.objects.get(id=primary_key)
			    num = t.get_athlete_names().index('%s' %(user))
			    temp_name = t.name
			    temp_time = t.start_time
			    temp_results = t.get_results().get('runners')[num]
			    temp_array = [{'Name': temp_name, 'Date': temp_time, 'Runner': temp_results}]
			    final_array = final_array + temp_array
			    final_array = final_array[::-1]
            return Response(final_array)
            sessions = final_array
            return Response(sessions)
        elif is_coach(user):
            return HttpResponse(status.HTTP_404_NOT_FOUND)

        # If not a user or coach, no results can be found.
        else:
            return HttpResponse(status.HTTP_404_NOT_FOUND)

        
class TimingSessionReset(views.APIView):
    #serializer_class = TimingSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    def post(self,request):
        data = request.POST 
        user = self.request.user
        
        # If the user is an athlete do not allow them to edit.
        if is_athlete(user):
            return HttpResponse(status.HTTP_403_FORBIDDEN)
        
        elif is_coach(user):
            try:
                sessions = TimingSession.objects.filter(manager=user)
                t = sessions.get(id=data['id'])
                t.tagtimes.clear()

                # Clear the cache for the session.
                cache.delete(('ts_%i_results' %t.id))
                cache.delete(('ts_%i_athlete_names' %t.id))
                return HttpResponse(status.HTTP_202_ACCEPTED)
            
            except:
				return HttpResponse(status.HTTP_404_NOT_FOUND)

class TimingSessionStartButton(views.APIView):
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.AllowAny,)#permissions.IsAuthenticated,)

    def post(self, request):
        """Sets the start button time to now."""
        current_time = timezone.now() 
        data = request.POST
        print data

        try:
            #sessions = TimingSession.objects.filter(manager=self.request.user)
            #ts = sessions.get(id=data['id'])
            ts = TimingSession.objects.get(id=data['id'])
            #print ts
            ts.start_button_time = current_time
            ts.save()
            return HttpResponse(status.HTTP_202_ACCEPTED)

        except:
			return HttpResponse(status.HTTP_404_NOT_FOUND)


class TimingSessionViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all sessions associated with the user.
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)

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

    def post_save(self, obj, created):
        """Assigns reader to workout after it saves"""
        user = self.request.user
        t=TimingSession.objects.latest('id')
        r=Reader.objects.filter(owner=user)
        t.readers.add(*r)
        t.save()    

def create_split(reader_id, tag_id, time):
    """Creates a new tagtime based on an incoming split."""

    # Get the tag and reader associated with the notification. Note that if the
    # tag or reader has not been established in the system, the split will be
    # ignored here.
    print reader_id
    print tag_id
    print time

    try:
        reader = Reader.objects.get(id_str=reader_id)
        tag = Tag.objects.get(id_str=tag_id)
    except:
        return -1
   
    print 'tag, reader found'
    # Create new TagTime.
    dtime = timezone.datetime.strptime(time, "%Y/%m/%d %H:%M:%S.%f") 
    #dtime = timezone.pytz.utc.localize(dtime)
    ms = int(str(dtime.microsecond)[:3])
    #dtime = timezone.now()
    #ms = 0
    tt = TagTime(tag_id=tag.id, time=dtime, reader_id=reader.id, milliseconds=ms)
    print 'tag time initialized'
    try:
        tt.save()
    except:
        return -1

    print 'tagtime created'

    # Add the TagTime to all sessions active and having a related reader.
    for s in reader.active_sessions:
        #if s.registered_tags.all() and (tag.timingsession_set.filter(id=s.id)):
        s.tagtimes.add(tt.pk)
        cache.delete(('ts_%i_results' %s.id))
        cache.delete(('ts_%i_athlete_names' %s.id))
        print 'added to active session'
        
    
    return 0


@csrf_exempt
@api_view(['POST','GET'])
@permission_classes((permissions.AllowAny,))
def post_splits(request):
    """Receives updates from readers."""

    if request.method == 'POST':
        data = request.POST
        print data
        reader_name = data['r']
        split_list = ast.literal_eval(data['s'])
        print reader_name
        print split_list
        
        split_status = 0
        for split in split_list:
            if create_split(reader_name, split[0], split[1]):
                split_status = -1

        if split_status:
            return HttpResponse(status.HTTP_400_BAD_REQUEST)
        else:
            return HttpResponse(status.HTTP_201_CREATED)

    elif request.method == 'GET':
        return Response({str(timezone.now())}, status.HTTP_200_OK)



    
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def verify_login(request):
    """
    Checks if the user is logged in. Returns a JSON response.
    """
    print request.user
    return HttpResponse()


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def create_race(request):
    """
    Creates a race by making a timing session and registering runners/tags.
    Posted data should be in the form:
        {race_name: '', 
         race_date: 'yyyy/mm/dd', 
         director_username: '',
         athletes: [{first_name: '', last_name: '', tag: '', team: ''}, ...]
        }
    """
    data = request.POST

    # Create the timing session.
    name = data['race_name']
    start_time = timezone.datetime.strptime(data['race_date'], "%Y/%m/%d") 
    stop_time = start_time+timezone.timedelta(1)
    ts = TimingSession.objects.create(name=name, start_time=start_time,
                                      stop_time=stop_time)

    # Assign the session to a coach.
    uc = User.objects.get_or_create(username=data['director_username'])
    c = CoachProfile.objects.get_or_create(user=uc)
    ts.manager = uc
    ts.save()

    # Get a list of all the teams in the race and register each one.
    team_list = []
    for athlete in data['athletes']:
        team_name = athletes['team']
        if team_name not in team_list:
            team_list.append(team)

    # Add each athlete to the race.
    for athlete in data['athletes']:

        # Create the user and athlete profile.
        first_name = athlete['first_name']
        last_name = athlete['last_name']
        username = first_name + last_name
        user = User.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   username=username)
        a = AthleteProfile.objects.create(user=user)

        # Create the rfid tag object and add to session.
        tag_id = athlete['tag']
        tag = Tag.objects.create(id_str=tag_id, user=user)
        ts.registered_tags.add(tag.pk)









@csrf_exempt
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def current_time(request):
    return Response({str(timezone.now())}, status.HTTP_200_OK)

