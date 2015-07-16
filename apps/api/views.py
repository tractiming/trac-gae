#sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core import serializers
from django.core.serializers import serialize
from django.utils.encoding import force_bytes
from django.template import loader, RequestContext

from rest_framework import viewsets, permissions, renderers, status, serializers, views
from rest_framework.response import Response
from rest_framework.decorators import link, api_view, permission_classes, detail_route
from rest_framework.parsers import MultiPartParser, FormParser

from provider.oauth2.models import Client, AccessToken


from serializers import (UserSerializer, RegistrationSerializer, TagSerializer, 
                         TimingSessionSerializer, ReaderSerializer, CoachSerializer,
                         CSVSerializer, ScoringSerializer)

from trac.models import (TimingSession, AthleteProfile, CoachProfile, 
                         Tag, Reader, TagTime)
from trac.util import is_athlete, is_coach
from util import create_split


import json
import ast
import dateutil.parser
import uuid
import hashlib
import base64

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
        user.email = request.DATA['email']
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
            coach.organization = data['organization']
            coach.save()

        # Add user to group
        group, created = Group.objects.get_or_create(name=data['organization'])
        user.groups.add(group.pk)
        user.save()

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
        """
        Overrides the default method to only return tags that belong to the
        user making the request.
        """
        user = self.request.user

        # If the user is an athlete, display the tags he owns.
        if is_athlete(user):
            tags = user.tag_set.all()

        # If the user is a coach, list the tags owned by any of his athletes.
        elif is_coach(user):
            tags = Tag.objects.filter(user__in=[a.user for a in
                user.coach.athletes.all()])
        
        # Otherwise, there are no tags to show.
        else:
            tags = Tag.objects.none()
        return tags

    def create(self, request, *args, **kwargs):
        if is_athlete(self.request.user):
            request.DATA[u'user'] = self.request.user.pk
        return super(TagViewSet, self).create(request, *args, **kwargs)

class CoachViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CoachSerializer

    def get_queryset(self):
        """
        Returns all coaches
        """
        try:
            cp = [c.user for c in CoachProfile.objects.all()]
        except ObjectDoesNotExist:
            cp = []

        return cp

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
        """ 
        Return only those readers belonging to the current user.
        """
        user = self.request.user
        readers = Reader.objects.filter(owner=user)
        return readers

    def pre_save(self, obj):
        """
        Assign the reader to this user.
        """
        obj.owner = self.request.user

class ScoringViewSet(viewsets.ModelViewSet):
    """
    Returns list of scored sessions
    """
    serializer_class = ScoringSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """
        Overrides default method to filter public sessions by organization.
        """
        org = self.request.GET.get('org', None)
        if org == 'Unaffiliated':
            # return sessions belonging to unaffiliated users
            managers = User.objects.filter(groups__isnull=True)
            sessions = TimingSession.objects.filter(private=False, manager__in=managers)
        elif org is not None:
            # return sessions belonging to users under requested organization
            managers = Group.objects.get(name=org).user_set.all()
            sessions = TimingSession.objects.filter(private=False, manager=managers[0])
        else:
            # return all public sessions
            sessions = TimingSession.objects.filter(private=False)
           
        return sessions  
        
class TimingSessionViewSet(viewsets.ModelViewSet):

    """
    Returns a list of all sessions associated with the user.
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """Overrides default method to filter sessions by user."""
        user = self.request.user
        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            ap = AthleteProfile.objects.get(user=user)
            sessions = ap.get_completed_sessions()
        
        # If the user is a coach, list all sessions he manages.
        elif is_coach(user):
            sessions = TimingSession.objects.filter(manager=user)
            
        # If not a user or coach, list all public sessions.
        else:
            sessions = TimingSession.objects.filter(private=False)
        return sessions    

    def pre_save(self, obj):
        """Assigns a manager to the workout before it is saved."""
        obj.manager = self.request.user

    def post_save(self, obj, created):
        """
        Assigns reader to workout after it saves. Right now, this just adds all
        of the readers currently owned by the user.
        """
        user = self.request.user
        t=TimingSession.objects.latest('id')
        r=Reader.objects.filter(owner=user)
        t.readers.add(*r)
        t.save()

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def open_session(request):
    """
    Opens a timing session by setting its start time to now and its stop time
    to one day from now.
    """
    data = request.POST
    try:
        ts = TimingSession.objects.get(id=data['id'])
        ts.start_time = timezone.now()-timezone.timedelta(seconds=8)
        ts.stop_time = ts.start_time+timezone.timedelta(days=1)
        ts.save()
        return HttpResponse(status.HTTP_202_ACCEPTED)

    except ObjectDoesNotExist:
		return HttpResponse(status.HTTP_404_NOT_FOUND)
            
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def close_session(request):
    """
    Closes a timing session by setting its stop time to now.
    """
    data = request.POST
    try:
        ts = TimingSession.objects.get(id=data['id'])
        ts.stop_time = timezone.now()
        ts._build_tag_archive()
        ts.save()
        return HttpResponse(status.HTTP_202_ACCEPTED)

    except ObjectDoesNotExist:
		return HttpResponse(status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def start_session(request):
    """
    Press the session's 'start button'. This sets the time that all the splits
    are calculated relative to. Effectively acts as the gun time.
    """
    data = request.POST
    # FIXME: This is a hack that offsets the delay the reader has in setting its
    # real time. 
    # Also note that the start time is taken to be the time the request hits
    # the server, not the time the button is pressed on the phone, etc.
    current_time = timezone.now()-timezone.timedelta(seconds=8)
    
    try:
        ts = TimingSession.objects.get(id=data['id'])
        ts.start_button_time = current_time
        ts.save()
        return HttpResponse(status.HTTP_202_ACCEPTED)
    except ObjectDoesNotExist:
		return HttpResponse(status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def reset_session(request):
    """
    Reset a timing session by clearing all of its tagtimes.
    """
    data = request.POST 
    user = request.user
        
    # If the user is an athlete do not allow them to edit.
    # TODO: define better permissions for this function.
    if not is_coach(user):
        return HttpResponse(status.HTTP_403_FORBIDDEN)
        
    else:
        try:
            sessions = TimingSession.objects.filter(manager=user)
            t = sessions.get(id=data['id'])
            t.tagtimes.clear()
            cache.delete(('ts_%i_results' %t.id))
            cache.delete(('ts_%i_athlete_names' %t.id))
            return HttpResponse(status.HTTP_202_ACCEPTED)
        
        except:
            return HttpResponse(status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def filtered_results(request):
    """
    Get the filtered results for a given session.
    """
    data = request.GET

    # Get the session.
    if 'id' in data:
        try:
            session = TimingSession.objects.get(id=data['id'])
        except ObjectDoesNotExist:
            return HttpResponse(status.HTTP_404_NOT_FOUND)

    else:
        return HttpResponse(status.HTTP_404_NOT_FOUND)

    # Filter age.
    if ('age_lte' in data) and ('age_gte' in data):
        age_range = [int(data['age_gte']), int(data['age_lte'])]
    else:
        age_range = []

    # Filter gender.
    if 'gender' in data:
        g = data['gender']
    else:
        g = ''

    results = session.get_filtered_results(gender=g, age_range=age_range)
    return Response(results, status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def team_results(request):
    """
    Return the team scores for a given session.
    """
    data = request.GET

    # Get the session.
    try:
        session = TimingSession.objects.get(id=data['id'])
    except ObjectDoesNotExist:
        return HttpResponse(status.HTTP_404_NOT_FOUND)

    team_results = session.get_team_results()
    return Response(team_results, status.HTTP_200_OK)

@csrf_exempt
@api_view(['POST','GET'])
@permission_classes((permissions.AllowAny,))
def post_splits(request):
    """
    Interacts with the readers. Readers post new splits and can get the
    current time. Readers don't handle permissions or csrf.
    """
    if request.method == 'POST':
        data = request.POST
        reader_name = data['r']
        split_list = ast.literal_eval(data['s'])
        
        split_status = 0
        for split in split_list:
            if create_split(reader_name, split[0], split[1]):
                split_status = -1

        if split_status:
            return HttpResponse(status.HTTP_400_BAD_REQUEST)
        else:
            return HttpResponse(status.HTTP_201_CREATED)

    # To avoid having to navigate between different urls on the readers, we use
    # this same endpoint to retrieve the server time. 
    elif request.method == 'GET':
        return Response({str(timezone.now())}, status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def edit_split(request):
    """
    Edit, delete, or insert a single split within a single workout.
    Parameters:
        - id: the id of the timing session
        - user_id: id of the user whose splits we want to change
        - action: one of 'edit', 'insert', or 'delete'
        - indx: index of the split to perform the action on
        - val: new value for edited or inserted split
    Note: all indices are in reference to unfiltered result set. An error will
    be raised if splits are edited in a session where filter_choice is True.
    """
    data = request.POST
    ts = TimingSession.objects.get(id=int(data['id']))
    all_tags = ts.tagtimes.values_list('tag_id', flat=True).distinct()
    tag = Tag.objects.filter(user_id=int(data['user_id']), id__in=all_tags)
    
    if data['action'] == 'edit':
        ts._edit_split(tag.id, int(data['indx']), float(data['val']))
    elif data['action'] == 'insert':
        ts._insert_split(tag.id, int(data['indx']), float(data['val']))
    elif data['action'] == 'delete':
        ts._delete_split(tag.id, int(data['indx']))
    else:
		return HttpResponse(status.HTTP_404_NOT_FOUND)

    return HttpResponse(status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def get_sessions_with_paginated_results(request):
    wid = int(request.GET.get('id'))
    begin = int(request.GET.get('i1'))
    stop = int(request.GET.get('i2'))
    user = request.user

    if is_coach(user):
        ts = TimingSession.objects.filter(manager=user)
    else:
        ts = TimingSession.objects.filter(private='false')
    new_ts = []
    for row in ts:
        if row.id == wid:
            run = row.get_results(m=begin, n=stop).get('runners')
            for r in run:
                temp_ts = {'id': row.id, 'name': row.name, 'runners': r}
                new_ts.append(temp_ts)
    return Response(new_ts, status.HTTP_200_OK)
#pagination endpoint
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def sessions_paginate(request):
    begin = int(request.GET.get('i1'))
    stop = int(request.GET.get('i2'))
    user = request.user
    # get pagination beginning and next page value
    start_date = request.GET.get('start_date')
    stop_date = request.GET.get('stop_date')
    if start_date == None or stop_date == None:   
        if is_coach(user):
            table = TimingSession.objects.filter(manager=user).values()
        else:
            table = TimingSession.objects.filter(private='false').values()
    else:
        start_date = dateutil.parser.parse(start_date)
        stop_date = dateutil.parser.parse(stop_date)        
        if is_coach(user):
            table = TimingSession.objects.filter(Q(manager=user) & Q(start_time__range=(start_date, stop_date))).values()
        else:
            table = TimingSession.objects.filter(Q(private='false') & Q(start_time__range=(start_date, stop_date))).values()
        #reset indices for pagination without changing id
    if begin == 0 and stop == 0:
        return Response(table, status.HTTP_200_OK)
    else:
        i = 1
        result = []
        for instance in table[::-1]:
            if i >= begin and i <= stop:
                #if indices are in the range of pagination, append to return list
                result.append(instance)
            i += 1
        result = list(reversed(result))
        return Response(result, status.HTTP_200_OK)

def string2bool(string):
    if string == 'true':
        return True
    elif string == 'false':
        return False

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def time_create(request):
    #time backend. Decided not to change any of the api's just make another intermediary endpoint that funnels from create.html into sessions model
    data = request.POST
    user = request.user
    begin_time = dateutil.parser.parse(data['start_time'])
    stop_time = dateutil.parser.parse(data['stop_time'])    #KEY: parsing date and time into datetime objects before putting into database.
    if int(data['id']) == 0: #for new instances
        ts, created = TimingSession.objects.get_or_create(name=data['name'], manager=user, start_time=begin_time, stop_time=stop_time, track_size=data['track_size'], interval_distance=data['interval_distance'], filter_choice=data['filter_choice'], private=string2bool(data['private']))
    else:
        ts= TimingSession.objects.get(id=int(data['id'])) #for updated instances
        ts.name = data['name']
        ts.manager = user
        ts.start_time = begin_time
        ts.stop_time = stop_time
        ts.track_size = data['track_size']
        ts.interval_distance = data['interval_distance']
        ts.filter_choice = data['filter_choice']
        ts.private = string2bool(data['private'])
    r = Reader.objects.filter(owner=user)
    ts.readers.add(*r)
    ts.save()
    return HttpResponse(status.HTTP_201_CREATED)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def create_race(request):
    """
    Creates a race by making a timing session and registering runners/tags.
    Posted data should be in the form:
        {race_name: '', 
         race_date: 'yyyy/mm/dd', 
         director_username: '',
         readers = [id1, id2, ...],
         athletes: [{first_name: '', last_name: '', tag: '', 
                     team: '', age: '', gender: ''}, ...]
        }
    """
    data = json.loads(request.body)
    # Assign the session to a coach.
    uc, created = User.objects.get_or_create(username=data['director_username'])
    c, created = CoachProfile.objects.get_or_create(user=uc)
    date = data['race_date']
    datestart = dateutil.parser.parse(date)
    dateover = datestart + timezone.timedelta(days=1)
    # Create the timing session.
    name = data['race_name']
    ts, created = TimingSession.objects.get_or_create(name=name, manager=uc, start_time=datestart, stop_time=dateover)
    if not created:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)

    # Create readers and add to the race.
    for r_id in data['readers']:
        try:
            r = Reader.objects.get(id_str=r_id)
        except ObjectDoesNotExist:
            r = Reader.objects.create(id_str=r_id, owner=uc, name=r_id)
        ts.readers.add(r.pk)
    ts.save()    

    # Get a list of all the teams in the race and register each one.
    teams = set([a['team'] for a in data['athletes'] if (a['team'] is not None)])
    for team in teams:
        Group.objects.get_or_create(name='%s-%s' %(data['race_name'], team))

    # Add each athlete to the race.
    for athlete in data['athletes']:

        # Create the user and athlete profile.
        first_name = athlete['first_name']
        last_name = athlete['last_name']
        username = first_name + last_name
        user, created = User.objects.get_or_create(first_name=first_name,
                                                   last_name=last_name,
                                                   username=username)
        a, created = AthleteProfile.objects.get_or_create(user=user)
        a.age = int(athlete['age'])
        a.gender = athlete['gender']
        a.save()

        # Create the rfid tag object and add to session.
        tag_id = athlete['tag']
        try:
            # If the tag already exists in the system, overwrite its user.
            tag = Tag.objects.get(id_str=tag_id)
            tag.user = user
            tag.save()
        except ObjectDoesNotExist:
            tag = Tag.objects.create(id_str=tag_id, user=user)
        except MultipleObjectsReturned:
            tag = Tag.objects.create(id_str= 'colliding tag', user=user)


        ts.registered_tags.add(tag.pk)
    return HttpResponse(status.HTTP_201_CREATED)

#registered tags endpoint for settings
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def WorkoutTags(request):
    if request.method == 'GET': #loadAthletes
        id_num = int(request.GET.get('id'))
        user = request.user
        array = []
        if not is_coach(user):
            return HttpResponse(status.HTTP_403_FORBIDDEN)
        else:
            table = TimingSession.objects.get(id=id_num)
            result = table.registered_tags.all()        
            for instance in result:
                u_name = instance.user.username
                array.append({'id': instance.id, 'user': u_name, 'id_str': instance.id_str})
            return Response(array, status.HTTP_200_OK)
    elif request.method == 'POST':
        id_num = request.POST.get('id')
        tag_id = request.POST.get('id2')
        i_user = request.user
        if not is_coach(i_user):
            return HttpResponse(status.HTTP_403_FORBIDDEN)
        else:
            if request.POST.get('submethod') == 'Delete': #Delete
                ts = TimingSession.objects.get(id=id_num)
                tag = ts.registered_tags.get(id=tag_id)
                ts.registered_tags.remove(tag)
                return HttpResponse(status.HTTP_200_OK)
            elif request.POST.get('submethod') == 'Update': #Update and Create
                ts = TimingSession.objects.get(id=id_num)
                user, created = User.objects.get_or_create(username=request.POST.get('username'))
                a, created = AthleteProfile.objects.get_or_create(user=user)
                if is_coach(i_user):
                    cp = CoachProfile.objects.get(user=i_user)
                    cp.athletes.add(a.pk)
                a.save()
                try:  #if tag exists update user. Or create tag.
                    tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                    tag.user = user
                    tag.save()
                except ObjectDoesNotExist:
                    try:
                        tag = Tag.objects.get(user = user)
                        tag.id_str = request.POST.get('id_str')
                        tag.save()
                    except ObjectDoesNotExist:
                        tag = Tag.objects.create(id_str=request.POST.get('id_str'), user=user)
                ts.registered_tags.add(tag.pk)
                ts.save()
                return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def ManyDefaultTags(request):
    i_user = request.user
    if not is_coach(i_user):
        return HttpResponse(status.HTTP_403_FORBIDDEN);
    else:
        data = json.loads(request.body)
        for athlete in data['athletes']:
            atl = User.objects.get(username=athlete['username'])
            ts = TimingSession.objects.get(id=data['id'])
            try:
                tag = Tag.objects.get(user = atl)
            except:
                tag = Tag.objects.create(user = atl)
                tag.id_str = 'edit tag'
            tag.save()
            ts.registered_tags.add(tag.pk)
        ts.save()
        return HttpResponse(status.HTTP_200_OK)

#update and remove athlete profiles from coach.athletes.all() but keeps the athlete's user account.
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def edit_athletes(request):
    i_user = request.user
    if not is_coach(i_user):
        return HttpResponse(status.HTTP_403_FORBIDDEN)
    else:
        if request.POST.get('submethod') == 'Delete': #Removes the link with coach account
            cp = CoachProfile.objects.get(user = i_user)
            atl = cp.athletes.get(user_id=request.POST.get('id'))
            cp.athletes.remove(atl)
        elif request.POST.get('submethod') == 'Update': #Change user's first and last names. Not change username.
            cp = CoachProfile.objects.get(user = i_user)
            atl = cp.athletes.get(user_id=request.POST.get('id'))
            atl.user.first_name = request.POST.get('first_name')
            atl.user.last_name = request.POST.get('last_name')
            atl.user.save()
        elif request.POST.get('submethod') == 'Create':
            cp = CoachProfile.objects.get(user = i_user)
            user, created = User.objects.get_or_create(username = request.POST.get('username'), first_name = request.POST.get('first_name'), last_name = request.POST.get('last_name'))
            atl, created = AthleteProfile.objects.get_or_create(user = user)
            #tag, created = Tag.objects.get_or_create(user = user, id_str = request.POST.get('id_str'))
            try:
                tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                tag.user = user
            except ObjectDoesNotExist:
                tag = Tag.objects.create(user = user, id_str = request.POST.get('id_str'))
            cp.athletes.add(atl.pk)
            tag.save()
            atl.save()
            user.save()
        return HttpResponse(status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def IndividualTimes(request):

    data = int(request.GET.get('id'))
    user = request.user
    # print for permissions
    
    # If the user is an athlete, list all the workouts he has run. If coach, the user he wants.
    # Uses the User.id, alternatively could use athelte.id
    if is_coach(user):
        ap = User.objects.get(id=data)
        print ap
    elif is_athlete(user):
        ap = user
        
    # If not a user or coach, no results can be found.
    else:
        return HttpResponse(status.HTTP_404_NOT_FOUND)
    final_array = [{'Name':ap.username}]
    sessions = ap.athlete.get_completed_sessions()
    #Iterate through each session to get all of a single users workouts
    for s in sessions:
        t = TimingSession.objects.get(id=s.pk)
        if ap.first_name != '' and ap.last_name != '':
            string1 = ap.first_name
            string2 = ap.last_name
            username = string1 +' '+string2
            num = t.get_athlete_names().index(username)
        else:
            username = ap.username
            num = t.get_athlete_names().index(ap.username)
        run = t.get_results().get('runners')
        for r in run:
            if r['name'] == username:
                temp = r
        temp_array = [{'Name': t.name, 'Date': t.start_time, 'id': t.id, 'Runner': temp}]
        final_array += temp_array
    final_array = final_array[::-1]
    return Response(final_array)

@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def token_validation(request):
    return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@login_required()
@permission_classes((permissions.AllowAny,))
def reset_password(request):
    name =  base64.urlsafe_b64decode(request.POST.get('user').encode('utf-8'))
    user = User.objects.get(pk = name)
    token = request.auth
    if token not in user.accesstoken_set.all():
            return HttpResponse(status.HTTP_403_FORBIDDEN)
    if token.expires < timezone.now():
            return HttpResponse(status.HTTP_403_FORBIDDEN)
    if user.is_authenticated():
        user.set_password(request.POST.get('password'))
        user.save()
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)
    user.accesstoken_set.get(token = token).delete()
    return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def send_email(request):
    email = request.POST.get('email')
    name = request.POST.get('user')
    u = User.objects.get(email = email)
    user2 = User.objects.get(username = name)
    if u == user2:
        uidb64 = base64.urlsafe_b64encode(force_bytes(u.pk))
        token = AccessToken(user = u, client = u.oauth2_client.get(user = u), expires = timezone.now()+timezone.timedelta(minutes=5))
        token.save()
        c = {
            'email': email,
            'domain': request.META['HTTP_HOST'],
            'site_name': 'TRAC',
            'uid': uidb64,
            'user': u,
            'token': str(token),
            'protocol': 'https',
        }
        url = c['domain'] + '/UserSettings/' + c['uid'] + '/' + c['token'] + '/'
        email_body = loader.render_to_string('../templates/email_template.html', c)
        send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com', [c['email'],], fail_silently=False)
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)
######################### Do we need these? ###########################
#@api_view(['GET'])
#@permission_classes((permissions.AllowAny,))
#def verify_login(request):
#    """
#    Checks if the user is logged in. Returns a JSON response.
#    """
#    print request.user
#    return HttpResponse()
#
#@csrf_exempt
#@api_view(['GET'])
#@permission_classes((permissions.AllowAny,))
#def current_time(request):
#    return Response({str(timezone.now())}, status.HTTP_200_OK)
#
#class JSONResponse(HttpResponse):
#    """
#    Renders contents to JSON.
#    """
#    def __init__(self, data, **kwargs):
#        content = renderers.JSONRenderer().render(data)
#        kwargs['content_type'] = 'application/json'
#        super(JSONResponse, self).__init__(content, **kwargs)
#class TimingSessionStartButton(views.APIView):
#    serializer_class = TimingSessionSerializer
#    permission_classes = (permissions.AllowAny,)#permissions.IsAuthenticated,)
#
#    def post(self, request):
#        """Sets the start button time to now."""
#        current_time = timezone.now()-timezone.timedelta(seconds=8)
#        data = request.POST
#        print data
#
#        try:
#            #sessions = TimingSession.objects.filter(manager=self.request.user)
#            #ts = sessions.get(id=data['id'])
#            ts = TimingSession.objects.get(id=data['id'])
#            #print ts
#            ts.start_button_time = current_time
#            ts.save()
#            return HttpResponse(status.HTTP_202_ACCEPTED)
#
#        except:
#			return HttpResponse(status.HTTP_404_NOT_FOUND)
#class TimingSessionReset(views.APIView):
#    #serializer_class = TimingSessionSerializer
#    permission_classes = (permissions.IsAuthenticated,)
#    def post(self,request):
#        data = request.POST 
#        user = self.request.user
#        
#        # If the user is an athlete do not allow them to edit.
#        if is_athlete(user):
#            return HttpResponse(status.HTTP_403_FORBIDDEN)
#        
#        elif is_coach(user):
#            try:
#                sessions = TimingSession.objects.filter(manager=user)
#                t = sessions.get(id=data['id'])
#                t.tagtimes.clear()
#
#                # Clear the cache for the session.
#                cache.delete(('ts_%i_results' %t.id))
#                cache.delete(('ts_%i_athlete_names' %t.id))
#                return HttpResponse(status.HTTP_202_ACCEPTED)
#            
#            except:
#				return HttpResponse(status.HTTP_404_NOT_FOUND)
#class IndividualTimes(views.APIView):
#    serializer_class = TimingSessionSerializer
#    permission_classes = (permissions.IsAuthenticated,)
#    def get(self, request, format=None):
#        
#        user = self.request.user
#        # print user
#        final_array = []
#        # If the user is an athlete, list all the workouts he has run.
#        if is_athlete(user):
#            ap = AthleteProfile.objects.get(user=user)
#            sessions = ap.get_completed_sessions()
#		#Iterate through each session
#            for s in sessions:
#			    primary_key = s.pk
#			    t = TimingSession.objects.get(id=primary_key)
#			    num = t.get_athlete_names().index('%s' %(user))
#			    temp_name = t.name
#			    temp_time = t.start_time
#			    temp_results = t.get_results().get('runners')[num]
#			    temp_array = [{'Name': temp_name, 'Date': temp_time, 'Runner': temp_results}]
#			    final_array = final_array + temp_array
#			    final_array = final_array[::-1]
#            return Response(final_array)
#            sessions = final_array
#            return Response(sessions)
#        elif is_coach(user):
#            return HttpResponse(status.HTTP_404_NOT_FOUND)
#
#        # If not a user or coach, no results can be found.
#        else:
#            return HttpResponse(status.HTTP_404_NOT_FOUND)
