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

from provider.oauth2.models import Client, AccessToken

from serializers import (UserSerializer, RegistrationSerializer, 
                         TagSerializer, TimingSessionSerializer,
                         ReaderSerializer, UserSerializer)

from trac.models import TimingSession, AthleteProfile, CoachProfile
from trac.models import Tag, Reader, TagTime
from trac.util import is_athlete, is_coach
from django.http import Http404
from django.core.cache import cache

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

class TimingSessionReset(views.APIView):
	serializer_class = TimingSessionSerializer
	permission_classes = (permissions.IsAuthenticated,)
	def post(self,request):
		data = request.POST
		# print data
		user = self.request.user

		# If the user is an athlete do not allow them to edit.
		if is_athlete(user):
			return HttpResponse(status.HTTP_403_FORBIDDEN)

		elif is_coach(user):
			try:
				sessions = TimingSession.objects.filter(manager=user)
				t = sessions.get(id=data['id'])
				t.tagtimes.clear()
				# print t
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

@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def post_splits(request):
    """Receives updates from readers."""
    data = request.POST

    # Get the tag and reader associated with the notification. Note that if the
    # tag or reader has not been established in the system, the split will be
    # ignored here.
    try:
        reader = Reader.objects.get(id_str=data['r'])
        tag = Tag.objects.get(id_str=data['id'])
    except: #ObjectDoesNotExist:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)
    
    # Create new TagTime.
    dtime = timezone.datetime.strptime(data['time'], "%Y/%m/%d %H:%M:%S.%f") 
    ms = int(str(dtime.microsecond)[:3])
    tt = TagTime(tag_id=tag.id, time=dtime, reader_id=reader.id, milliseconds=ms)
    try:
        tt.save()
    except IntegrityError:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)

    # Add the TagTime to all sessions active and having a related reader.
    for s in reader.active_sessions:
        s.tagtimes.add(tt.pk)
        cache.delete(('ts_%i_results' %s.id))
        cache.delete(('ts_%i_athlete_names' %s.id))
    
    return HttpResponse(status.HTTP_201_CREATED)
    
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def verify_login(request):
    """
    Checks if the user is logged in. Returns a JSON response.
    """
    print request.user
    return HttpResponse()
