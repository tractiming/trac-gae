from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
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
from paypal.standard.forms import PayPalPaymentsForm


from serializers import (RegistrationSerializer, AthleteSerializer,TagSerializer,
                         TimingSessionSerializer, ReaderSerializer, CoachSerializer,
                         ScoringSerializer, TeamSerializer)

from trac.models import (TimingSession, Athlete, Coach, Tag, Reader, Split,
                         Team, PerformanceRecord)
from trac.util import is_athlete, is_coach
from util import create_split
from settings.common import PAYPAL_RECEIVER_EMAIL
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received


import json
import ast
import dateutil.parser
import uuid
import hashlib
import base64
import datetime
import math
import stats
import logging
logging.basicConfig()

default_distances=[100, 200, 400, 800, 1000, 1500, 1609, 2000, 3000, 5000, 10000]
default_times=[14.3, 27.4, 61.7, 144.2, 165, 257.5, 278.7, 356.3, 550.8, 946.7, 1971.9, ]

class verifyLogin(views.APIView):
	permission_classes = ()
	def post(self,request):
		data = request.POST
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
			cp = Coach.objects.get(user=user)
		except: #NotCoach:
			try:
				ap = Athlete.objects.get(user=user)
			except: #NotAthlete
				return HttpResponse(status.HTTP_404_NOT_FOUND)
			return HttpResponse("athlete")
		return HttpResponse("coach")

# FIXME: add to timingsession serializer.
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
            athlete = Athlete()
            athlete.user = user
            athlete.save()

            try:
                team = Team.objects.get(name=data['organization'])
            except ObjectDoesNotExist:
                team = None

            if team:
                athlete.team = team
                athlete.save()

        elif user_type == 'coach':
            # Register a coach.
            coach = Coach()
            coach.user = user
            #coach.organization = data['organization']
            coach.save()

            # Add user to group - TODO: should they be auto-added to group?
            team, created = Team.objects.get_or_create(name=data['organization'],
                                                       coach=coach)
            if created:
                team.coach = coach 
                team.save()

            #Creates the Default table for coaches when they register.
            cp = Coach.objects.get(user=user)
            for i in range(0, len(default_distances)):
                r = PerformanceRecord.objects.create(distance=default_distances[i], time=default_times[i])
                cp.performancerecord_set.add(r)

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
            tags = Tag.objects.filter(athlete_id=user.athlete.id)

        # If the user is a coach, list the tags owned by any of his athletes.
        elif is_coach(user):
            tags = Tag.objects.filter(athlete__team__in=user.coach.team_set.all())
        
        # Otherwise, there are no tags to show.
        else:
            tags = Tag.objects.none()
        return tags


class CoachViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CoachSerializer
    queryset = Coach.objects.all()


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TeamSerializer
    
    def get_queryset(self):
        if is_coach(self.request.user):
            return self.request.user.coach.team_set.all()
    
        else:
            return Team.objects.filter(athlete__in=[self.request.user.athlete.pk])

    def pre_save(self, obj):
        obj.coach = self.request.user.coach


class AthleteViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AthleteSerializer

    def get_queryset(self):
        """
        Override the default method to return the users that are associated
        with an athlete belonging to this coach.
        """
        user = self.request.user
        if is_coach(user):
            coach = Coach.objects.get(user=user)
            return Athlete.objects.filter(team__in=coach.team_set.all())

        else:
            return Athlete.objects.get(user=user)

    def pre_save(self, obj):
        user = User.objects.create(username=self.request.DATA.get('username'))
        obj.user = user


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
        if is_coach(user):
            readers = Reader.objects.filter(coach=user.coach)
        else:
            reader = []
        return readers

    def pre_save(self, obj):
        """
        Assign the reader to this user.
        """
        obj.coach = self.request.user.coach


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
            ap = Athlete.objects.get(user=user)
            sessions = ap.get_completed_sessions()
        
        # If the user is a coach, list all sessions he manages.
        elif is_coach(user):
            sessions = TimingSession.objects.filter(coach=user.coach)
            
        # If not a user or coach, list all public sessions.
        else:
            sessions = TimingSession.objects.filter(private=False)
        return sessions    
    
    def pre_save(self, obj):
        """Assigns a manager to the workout before it is saved."""
        obj.coach = self.request.user.coach
        if not obj.start_time:
            obj.start_time = timezone.now()
        if not obj.stop_time:
            obj.stop_time = timezone.now()

    def post_save(self, obj, created):
        """
        Assigns reader to workout after it saves. Right now, this just adds all
        of the readers currently owned by the user.
        """
        readers = Reader.objects.filter(coach=self.request.user.coach)
        obj.readers.add(*readers)
        obj.save()
    
    @detail_route(methods=['get'])
    def individual_results(self, request, pk=None):
        limit = request.GET.get('limit', None)
        offset = request.GET.get('offset', None)

        if limit is not None and offset is not None:
            limit = int(limit)
            offset = int(offset)

        session = TimingSession.objects.get(pk=pk)
        raw_results = session.individual_results(limit, offset)

        results = {'num_results': session.num_athletes, 
                   'num_returned': len(raw_results),
                   'results': [{'name': r.name,
                                'id': r.user_id,
                                'splits': [[str(s)] for s in r.splits],
                                'total': str(r.total)
                               } for r in raw_results]
                   }
    
        return Response(results)

    @detail_route(methods=['get'])
    def team_results(self, request, pk=None):
        session = TimingSession.objects.get(pk=pk)
        raw_results = session.team_results()

        results = []
        for place, result in enumerate(raw_results):
            team_result = result
            team_result['place'] = place+1
            results.append(team_result)

        return Response(results)

    @detail_route(methods=['get'])
    def filtered_results(self, request, pk=None):
        gender = request.GET.get('gender', '')
        age_lte = int(request.GET.get('age_lte', 100))
        age_gte = int(request.GET.get('age_gte', 0))
        teams = request.GET.get('team', [])
        
        if teams and not isinstance(teams, list):
            teams = [teams]
    
        session = TimingSession.objects.get(pk=pk)
        raw_results = session.filtered_results(gender=gender,
                age_range=[age_gte, age_lte], teams=teams)
        
        results = {'num_returned': len(raw_results),
                   'results': [{'name': r.name,
                                'splits': [[str(s) for s in r.splits]],
                                'total': str(r.total)
                               } for r in raw_results]
                   }

        return Response(results)

    @detail_route(methods=['post'], permission_classes=[])
    def reset(self, request, pk=None):
        """
        Reset a timing session by clearing all of its tagtimes.
        """
        session = TimingSession.objects.get(pk=pk)
        session.clear_results()
        return HttpResponse(status.HTTP_202_ACCEPTED)
            

# TODO: Move to TimingSessionViewSet
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
            
# TODO: Move to TimingSessionViewSet
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

# TODO: Move to TimingSessionViewSet
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
    timestamp = int((current_time-timezone.datetime(1970, 1, 1)).total_seconds()*1000)

    try:
        ts = TimingSession.objects.get(id=data['id'])
        ts.start_button_time = timestamp
        ts.save()
        return HttpResponse(status.HTTP_202_ACCEPTED)
    except ObjectDoesNotExist:
		return HttpResponse(status.HTTP_404_NOT_FOUND)
    
# TODO: Move to TimingSessionViewSet
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
            session = TimingSession.objects.get(id=data['id'])
            session.clear_results()
            return HttpResponse(status.HTTP_202_ACCEPTED)
        
        except:
            return HttpResponse(status.HTTP_404_NOT_FOUND)

# TODO: DEPRECATED
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

    # Filter by team.
    if 'team' in data:
        t = [data['team']]
    else:
        t = []

    results = session.filtered_results(gender=g, age_range=age_range, teams=t)
    return Response(results, status.HTTP_200_OK)

#TODO: DEPRECATED
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
        ts._edit_split(tag[0].id, int(data['indx']), float(data['val']))
    elif data['action'] == 'insert':
        ts._insert_split(tag[0].id, int(data['indx']), float(data['val']), True)
    elif data['action'] == 'delete':
        ts._delete_split(tag[0].id, int(data['indx']))
    elif data['action'] == 'split':
        ts._insert_split(tag[0].id, int(data['indx']), float(data['val']), False)
    elif data['action'] == 'total_time':
        ts._overwrite_final_time(tag[0].id, int(data['hour']), int(data['min']), int(data['sec']), int(data['mil']))
    else:
        return HttpResponse(status.HTTP_404_NOT_FOUND)

    return HttpResponse(status.HTTP_202_ACCEPTED)
    
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
            table = TimingSession.objects.filter(coach=user.coach).values()
        else:
            table = TimingSession.objects.filter(private='false').values()
    else:
        start_date = dateutil.parser.parse(start_date)
        stop_date = dateutil.parser.parse(stop_date)        
        if is_coach(user):
            table = TimingSession.objects.filter(Q(coach=user.coach) & Q(start_time__range=(start_date, stop_date))).values()
        else:
            table = TimingSession.objects.filter(Q(private='false') & Q(start_time__range=(start_date, stop_date))).values()
        #reset indices for pagination without changing id
    if begin == 0 and stop == 0:
        return Response({'results': table, 'num_sessions': len(table)}, status.HTTP_200_OK)
    else:
        i = 1
        result = []
        for instance in table[::-1]:
            if i >= begin and i <= stop:
                #if indices are in the range of pagination, append to return list
                result.append(instance)
            i += 1
        #result = list(reversed(result))
        return Response({'results': result, 'num_sessions': len(table)}, status.HTTP_200_OK)

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
        ts, created = TimingSession.objects.get_or_create(name=data['name'],
                            coach=user.coach, start_time=begin_time,
                            stop_time=stop_time, track_size=data['track_size'],
                            interval_distance=data['interval_distance'],
                            filter_choice=string2bool(data['filter_choice']),
                            private=string2bool(data['private']))
    else:
        ts= TimingSession.objects.get(id=int(data['id'])) #for updated instances
        ts.name = data['name']
        ts.coach = user.coach
        ts.start_time = begin_time
        ts.stop_time = stop_time
        ts.track_size = data['track_size']
        ts.interval_distance = data['interval_distance']
        ts.filter_choice = string2bool(data['filter_choice'])
        ts.private = string2bool(data['private'])
    r = Reader.objects.filter(coach=user.coach)
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
    c, created = Coach.objects.get_or_create(user=uc)
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
    #teams = set([a['team'] for a in data['athletes'] if (a['team'] is not None)])
    #for team in teams:
    

    # Add each athlete to the race.
    for athlete in data['athletes']:

        # Create the user and athlete profile.
        first_name = athlete['first_name']
        last_name = athlete['last_name']
        username = first_name + last_name
        user, created = User.objects.get_or_create(first_name=first_name,
                                                   last_name=last_name,
                                                   username=username)
        a, created = Athlete.objects.get_or_create(user=user)
        g, created = Group.objects.get_or_create(name='%s-%s' %(data['race_name'], athlete['team']))
        a.user.groups.add(g.pk)
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
        # FIXME: What does this do?
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
                u_first = instance.user.first_name
                u_last = instance.user.last_name
                username = instance.user.username
                array.append({'id': instance.id, 'first': u_first, 'last': u_last, 'username': username, 'id_str': instance.id_str})
            return Response(array, status.HTTP_200_OK)
    elif request.method == 'POST':
        id_num = request.POST.get('id')
        tag_id = request.POST.get('id2')
        fname = request.POST.get('firstname')
        lname = request.POST.get('lastname')
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
                a, created = Athlete.objects.get_or_create(user=user)
                if is_coach(i_user):
                    cp = Coach.objects.get(user=i_user)
                    cp.athletes.add(a.pk)
                a.save()
                try:  #if tag exists update user. Or create tag.
                    user.first_name = fname
                    user.last_name = lname
                    tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                    tag.user = user
                    tag.save()
                    user.save()
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
                tag = Tag.objects.get(athlete=atl.athlete)
            except:
                tag = Tag.objects.create(athlete=atl.athlete)
                tag.id_str = 'edit tag'
            tag.save()
            ts.registered_tags.add(tag.pk)
        ts.save()
        return HttpResponse(status.HTTP_200_OK)

# TODO: Move to AthleteViewSet
#update and remove athlete profiles from coach.athletes.all() but keeps the athlete's user account.
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def edit_athletes(request):
    i_user = request.user
    if not is_coach(i_user):
        return HttpResponse(status.HTTP_403_FORBIDDEN)
    else:
        if request.POST.get('submethod') == 'Delete': #Removes the link with coach account
            cp = Coach.objects.get(user = i_user)
            atl = Athlete.objects.get(id=request.POST.get('id'))
            cp.athletes.remove(atl)
        elif request.POST.get('submethod') == 'Update': #Change user's first and last names. Not change username.
            cp = Coach.objects.get(user = i_user)
            atl = Athlete.objects.get(id=request.POST.get('id'))
            atl.user.first_name = request.POST.get('first_name')
            atl.user.last_name = request.POST.get('last_name')
            atl.user.save()
            try:  #if tag exists update user. Or create tag.
                tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                tag.user = atl.user
                tag.save()
            except ObjectDoesNotExist:
                try:
                    tag = Tag.objects.get(athlete = atl)
                    tag.id_str = request.POST.get('id_str')
                    tag.save()
                except ObjectDoesNotExist:
                    tag = Tag.objects.create(id_str=request.POST.get('id_str'), user=atl.user)
            return HttpResponse(status.HTTP_200_OK)

        elif request.POST.get('submethod') == 'Create':
            cp = Coach.objects.get(user = i_user)
            user, created = User.objects.get_or_create(username = request.POST.get('username'), first_name = request.POST.get('first_name'), last_name = request.POST.get('last_name'))
            atl, created = Athlete.objects.get_or_create(user = user)
            #tag, created = Tag.objects.get_or_create(user = user, id_str = request.POST.get('id_str'))
            try:
                tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                tag.user = user
            except ObjectDoesNotExist:
                tag = Tag.objects.create(athlete = user.athlete, id_str = request.POST.get('id_str'))
            #cp.athletes.add(atl.pk)
            tag.save()
            atl.save()
            user.save()
        return HttpResponse(status.HTTP_200_OK)

# TODO: Move to UserViewSet
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def edit_info(request):
    data = request.POST
    user = request.user
    team, created = Team.objects.get_or_create(name = data['org'], 
                                               coach=user.coach)

    # Do not reassign the coach if the team already exists. 
    if created:
        team.coach = user.coach
        team.save()

    user.username = data['name']
    user.email = data['email']
    user.save()
    return Response(status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def get_info(request):
    user = request.user
    try:
        email = user.email
    except:
        email = ""
    result = {'org': user.groups.get(id=1).name, 'name': user.username, 'email': email}
    return Response(result, status.HTTP_200_OK)

# TODO: Move to athletes endpoint.
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def IndividualTimes(request):

    athlete_id = int(request.GET.get('id'))
    user = request.user
    
    # Get the user's name.
    athlete = Athlete.objects.get(id=athlete_id)
    name = athlete.user.get_full_name()
    if not name:
        name = athlete.user.username

    sessions = [session for session in TimingSession.objects.all() if
                athlete_id in session.splits.values_list('athlete_id',
                flat=True).distinct()]
    results = {'name': name, 'sessions': []} 

    #Iterate through each session to get all of a single users workouts
    for session in sessions:

        session_results = session.calc_athlete_splits(athlete_id)
        session_info = {'id': session.id,
                        'name': session.name,
                        'date': session.start_time,
                        'splits': session_results[3],
                        'total': session_results[4]
                        }
        results['sessions'].append(session_info)

    return Response(results)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def upload_workouts(request):
    """ 
    Create a complete workout through CSV file upload.
    Parameters:
        - title: workout title
        - start_time: start date of workout in ISO string format
        - track_size: size of track
        - interval_distance: distance for each split
        - results: list of dictionary of workout results as follows
            - username: athlete username
            - first_name: athlete first name (used to create new athlete if doesn't exist)
            - last_name: athlete last name (used to create new athlete if doesn't exist)
            - splits: list of split times
    Note: The created workout will be automatically set to filter splits and private.
    """
    data = json.loads(request.body)
    user = request.user

    if not is_coach(user):
        return HttpResponse(status.HTTP_403_FORBIDDEN)

    coach = user
    start_time = dateutil.parser.parse(data['start_time'])
    #stop_time = dateutil.parser.parse(data['start_time'])

    ts = TimingSession(name=data['title'], manager=coach, start_time=start_time, stop_time=start_time, track_size=data['track_size'], interval_distance=data['interval_distance'], filter_choice=False, private=True)

    # set start button time to start time
    ts.start_button_time = start_time
    ts.save()

    results = data['results']
    if results:
        
        reader, created = Reader.objects.get_or_create(id_str='ArchivedReader', 
                defaults={ 'name': 'Archived Reader', 'owner': coach })
        ts.readers.add(reader.pk)

        for runner in results:
            new_user, created = User.objects.get_or_create(username=runner['username'], 
                    defaults={ 'first_name': runner['first_name'], 'last_name': runner['last_name'], 'email': coach.email, 'password': 'password' })
            if created:
                # Register new athlete.
                athlete = Athlete()
                athlete.user = new_user
                athlete.save()

                # add coach's org to new athlete's org
                if coach.groups.all():
                    group = coach.groups.all()[0]
                    new_user.groups.add(group.pk)
                    new_user.save()

                # Create the OAuth2 client.
                #name = user.username
                #client = Client(user=user, name=name, url=''+name,
                #        client_id=name, client_secret='', client_type=1)
                #client.save()
            
            tags = Tag.objects.filter(user=new_user)
            if tags:
                tag = tags[0]
            else:
                tag = Tag.objects.create(id_str=runner['username'], user=new_user)

            # create reference tagtime
            s_tt = TagTime(time=ts.start_button_time, milliseconds=0)
            time = s_tt.full_time

            for split in runner['splits']:
                try:
                    x = timezone.datetime.strptime(split, "%M:%S.%f")
                except:
                    x = timezone.datetime.strptime(split, "%S.%f")

                time += timezone.timedelta(minutes=x.minute,seconds=x.second,microseconds=x.microsecond)

                tt = TagTime.objects.create(tag_id=tag.id, time=time, reader_id=reader.id, milliseconds=time.microsecond/1000)
                ts.tagtimes.add(tt.pk)

    return HttpResponse(status.HTTP_201_CREATED)

@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def token_validation(request):
    return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
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
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def change_password(request):
    user = request.user
    token = request.auth
    if token not in user.accesstoken_set.all():
            return HttpResponse(status.HTTP_403_FORBIDDEN)
    if token.expires < timezone.now():
            return HttpResponse(status.HTTP_403_FORBIDDEN)
    if user.is_authenticated():
        p_verify = request.POST.get('o_password')
        if check_password(p_verify, user.password):
            user.set_password(request.POST.get('password'))
            user.save()
        else:
            return HttpResponse(status.HTTP_403_FORBIDDEN)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)
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
            'protocol': 'https://',
        }
        url = c['domain'] + '/UserSettings/' + c['uid'] + '/' + c['token'] + '/'
        email_body = loader.render_to_string('../templates/email_template.html', c)
        send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com', [c['email'],], fail_silently=False)
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def tutorial_limiter(request):
    user = request.user
    if timezone.now()- user.date_joined < datetime.timedelta(60):
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def VO2Max(request):
    user = request.user
    if is_coach(user):
        result = []
        cp = Coach.objects.get(user = user)
        for athlete in cp.athletes.all():
            sum_VO2 = 0
            count = 0
            for entry in athlete.performancerecord_set.all():
                sum_VO2 += entry.VO2
                count += 1
            try:
                avg_VO2 = sum_VO2 / count
                if entry.interval == 'i':
                    avg_VO2 = avg_VO2 / .9
                else:
                    avg_VO2 = avg_VO2 / .8
                avg_VO2 = int(avg_VO2)
                vVO2 = 2.8859 + .0686 * (avg_VO2 - 29)
                vVO2 = vVO2 / .9
            except:
                avg_VO2 = 'None'
                vVO2 = 1
            #print athlete
            #print 'VO2: ' + str(avg_VO2)
            #print 'vVO2: ' + str(vVO2)
            #print '100m: ' + str(100/vVO2)
            #print '200m: ' + str(200/vVO2)
            #print '400m: ' + str(400/vVO2)
            #print '800m: ' + str(800/vVO2)
            #print '1000m: ' + str(1000/vVO2)
            #print '1500m: ' + str(1500/vVO2)
            #print '1609m: ' + str(1609/vVO2)
            #print '3000m: ' + str(3000/vVO2)
            #print '5000m: ' + str(5000/vVO2)
            #print '10000m: ' + str(10000/vVO2)
    elif is_athlete(user):
        ap = Athlete.objects.get(user = user)

    return HttpResponse(status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def analyze(request):
    """
    Returns auto_edit splits.
    """

    #SETUP and parse dataList
    user = request.user
    idx = request.POST.get('id')
    ts = TimingSession.objects.get(id = idx)
    run = ts.individual_results()
    dataList = []
    for r in run:
        times = r[3]
        for index, item in enumerate(times):
            times[index] = float(item)
        name = r[0]
        dataList.append({'name': name, 'times': times})

    r_dict = stats.investigate(dataList)

    return Response (r_dict, status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
@login_required
@csrf_exempt
def subscription(request):
    user = request.user
    r = Reader.objects.filter(coach=user.coach)
    num_readers = len(r)
    price = float(25 * num_readers)
    paypal_dict = {
        "cmd": "_xclick-subscriptions",
        "business": PAYPAL_RECEIVER_EMAIL,
        "rm": 2,
        "a3": "25.00",
        "p3": 1,
        "t3": "M",
        "src": "1",
        "sra": "1",
        "no_note": "1",
        "payer_id": user.username,
        "item_name": "TRAC DATA",
        "notify_url": "https://trac-us.appspot.com/api/notify",
        "return_url": "https://trac-us.appspot.com/home",
        "cancel_return": "https://trac-us.appspot.com/home",
    }
    form = PayPalPaymentsForm(initial=paypal_dict, button_type="subscribe")
    context = {"form": form}
    return render(request, "payment.html", context)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def est_distance(request):
    """
    Updates user individual time tables using distance prediction.
    """

    #SETUP and parse dataList
    user = request.user
    idx = request.POST.get('id')
    ts = TimingSession.objects.get(id = idx)
    run = ts.individual_results()
    dataList = []
    for r in run:
        times = r[3]
        for index, item in enumerate(times):
            times[index] = float(item)
        name = r[0]
        dataList.append({'name': name, 'times': times})

    #Analysis split_times is distance prediction, r_times is individual runner times, and r_dicts is auto_edit dictionary
    split_times, r_times = stats.calculate_distance(dataList)

    #Interpolate split_times to data in coach's table.
    #Predict the distance run.
    cp = Coach.objects.get(user=user)
    r = cp.performancerecord_set.all()
    distanceList = []
    for interval in split_times.keys():
        int_time = split_times[interval]
        time_delta = 1000000
        for row in r:
            if abs(int_time-row.time) < time_delta:
                time_delta = abs(int_time-row.time)
                selected = row.distance

        #validate distance predictions with coach and update coach table as necessary.
        var = raw_input("Did you run a "+str(selected)+" in "+str(interval-1)+" splits?")
        if var == 'no':
            var2 = raw_input("What was the distance? ")
            if var2 == 'none':
                continue
            else:
                length = int(var2)
                s = cp.performancerecord_set.get(distance = length)
                s.time = (s.time + int_time)/2
                s.save()
                distanceList.append({'Splits': interval-1, 'Distance': length})
        else:
            distanceList.append({'Splits': interval-1, 'Distance': selected})

    #update each individual runner tables with their own data for distances predicted above.
    for runner in r_times:
        username = runner['name']
        a_user = User.objects.get(id = username)
        ap = Athlete.objects.get(user = a_user)
        cp.athletes.add(ap)
        for results in runner['results']:
            splits = results['splits']
            times = results['times']
            for distance in distanceList:
                if splits == distance['Splits'] and times != 0:
                    try:
                        r= ap.performancerecord_set.get(distance= distance['Distance'], interval= results['interval'])
                        r.time = (r.time + times)/2
                        velocity = r.distance / (r.time/60)
                        VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * r.time/60)) + .2989558 * pow(2.78, (-.1932605 * r.time/60)))
                        VO2 = int(VO2)
                        r.VO2 = VO2
                        r.save()
                    except:
                        velocity = distance['Distance']/ (times/60)
                        VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * times/60)) + .2989558 * pow(2.78, (-.1932605 * times/60)))
                        VO2 = int(VO2)
                        r = PerformanceRecord.objects.create(distance=distance['Distance'], time=times, interval= results['interval'], VO2= VO2)
                    ap.performancerecord_set.add(r)

    #return auto_edits 
    return HttpResponse(status.HTTP_200_OK)

@api_view(['GET'])
@login_required
@permission_classes((permissions.IsAuthenticated,))
def checkpayment(request):
    """Lock user out of site if they haven't paid."""
    u = request.user
    cp = Coach.objects.get(user=u)
    if cp.payment == 'completed':
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)

def ipnListener(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        # Undertake some action depending upon `ipn_obj`.
        user = ipn_obj.payer_id
        try:
            uu = User.objects.get(username = user)
            cp = Coach.objects.get(user = uu)
            cp.payment = 'completed'
            cp.save()
        except:
            pass

valid_ipn_received.connect(ipnListener)

