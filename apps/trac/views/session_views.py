from trac.models import TimingSession, Reader, Tag, Split, Team, Athlete
from trac.serializers import TimingSessionSerializer
from trac.utils.user_util import is_athlete, is_coach
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, detail_route
import json
import datetime
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import dateutil.parser


EPOCH = timezone.datetime(1970, 1, 1)


class TimingSessionViewSet(viewsets.ModelViewSet):
    """
    Return a list of all sessions associated with the user.
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """Override default method to filter sessions by user."""
        user = self.request.user

        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            # FIXME: this is no longer implemented.
            return TimingSession.objects.none()
            #ap = Athlete.objects.get(user=user)
            #sessions = ap.get_completed_sessions()
        
        # If the user is a coach, list all sessions he manages.
        elif is_coach(user):
            return TimingSession.objects.filter(coach=user.coach)
            
        # If not a user or coach, list all public sessions.
        else:
            return TimingSession.objects.filter(private=False)
    
    @csrf_exempt
    @detail_route(methods=['post'])
    def reset(self, request, *args, **kwargs):
        """
        Reset a timing session by clearing all of its tagtimes.
        """
        session = self.get_object()
        session.clear_results()
        return Response({}, status=status.HTTP_202_ACCEPTED)
    
    @csrf_exempt
    @detail_route(methods=['post'])
    def open(self, request, *args, **kwargs):
        """
        Open a session by setting its start time to now and its stop time
        to one day from now.
        """
        session = self.get_object()
        session.start_time = timezone.now()-timezone.timedelta(seconds=8)
        session.stop_time = session.start_time+timezone.timedelta(days=1)
        session.save()
        return Response({}, status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['post'],
                  permission_classes=[permissions.IsAuthenticated])
    def close(self, request, *args, **kwargs):
        """
        Close a session by setting its stop time to now.
        """
        session = self.get_object()
        session.stop_time = timezone.now()
        session.save()
        return Response({}, status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['POST'])
    def start_timer(self, request, *args, **kwargs):
        """
        Press the session's 'start button'. This sets the time that all the
        splits are calculated relative to. Effectively acts as the gun time.
        """
        # FIXME: This is a hack that offsets the delay the reader has in
        # setting its real time.  Also note that the start time is taken to be
        # the time the request hits the server, not the time the button is
        # pressed on the phone, etc.
        current_time = datetime.datetime.utcnow()-datetime.timedelta(seconds=8)
        timestamp = int((current_time-
            timezone.datetime(1970, 1, 1)).total_seconds()*1000)

        session = self.get_object()
        session.start_button_time = timestamp
        session.save()
        return Response({}, status.HTTP_202_ACCEPTED)

    @detail_route(methods=['get'])
    def individual_results(self, request, *args, **kwargs):
        limit = int(request.GET.get('limit', 1000))
        offset = int(request.GET.get('offset', 0))

        session = self.get_object()
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
        session = self.get_object()
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

        session = self.get_object()
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
    def add_missed_runner(self, request, pk=None):
        """
        Add a split for a registered tag never picked up by the reader.
        """
        data = request.POST

        ts = TimingSession.objects.get(pk=pk)
        reg_tags = ts.registered_tags.all()

        tag = Tag.objects.get(id=data['tag_id'], id__in=reg_tags)

        # get reader
        reader = ts.readers.all()[0]

        # create reference split
        if ts.start_button_time is not None:
            time = ts.start_button_time
        else:
            time = 0
        
        # create final split
        hours = int(data.get('hour', 0))
        mins = int(data.get('min', 0))
        secs = int(data.get('sec', 0))
        ms = int(data.get('mil', 0))

        diff = hours * 3600000 + mins * 60000 + secs * 1000 + ms
        time += diff

        tt = Split.objects.create(tag_id=tag.id, athlete_id=tag.athlete.id,
                                  time=time, reader_id=reader.id)
        ts.splits.add(tt.pk)

        return Response({}, status=status.HTTP_202_ACCEPTED)


    @detail_route(methods=['get'], permission_classes=[])
    def tfrrs(self, request, pk=None):
        """
        Create a TFRRS formatted CSV text string for the specified workout ID.
        """
        data = request.GET
        user = request.user
        coach = user.coach

        if not is_coach(user):
            return Response({}, status.HTTP_403_FORBIDDEN)

        ts = TimingSession.objects.get(pk=pk, coach=coach)

        tag_ids = ts.splits.values_list('tag_id', flat=True).distinct()
        raw_results = ts.individual_results()

        results = []
        for i, r in enumerate(raw_results):
            athlete = Athlete.objects.get(id=r.user_id)
            runner = athlete.user
            team = athlete.team
            birth_date = athlete.birth_date
            tag = Tag.objects.get(id__in=tag_ids, athlete=athlete)

            bib = tag.id_str
            TFFRS_ID = athlete.tfrrs_id or ''
            team_name = team.name or ''
            team_code = team.tfrrs_code or ''
            first_name = runner.first_name or ''
            last_name = runner.last_name or ''
            gender = athlete.gender or ''
            year = ''
            date_of_birth = str(birth_date.year)+'-'+ \
                            str(birth_date.month)+'-'+ \
                            str(birth_date.day) if birth_date else ''
            event_code = str(ts.interval_distance) or ''
            event_name = ts.name or ''
            event_division = ''
            event_min_age = ''
            event_max_age = ''
            sub_event_code = ''
            mark = str(r.total)
            metric = '1'
            fat = '0'
            place = str(i+1)
            score = place
            heat = ''
            heat_place = ''
            rnd = ''
            points = ''
            wind = ''
            relay_squad = ''

            # Untested, but should be the way to go.
            #results.append(','.join([bib, TFFRS_ID, team_name, team_code,
            #               first_name, last_name, gender, year, date_of_birth,
            #               event_code, event_name, event_division,
            #               event_min_age, event_max_age, sub_event_code, mark,
            #               metric, fat, place, score, heat, heat_place, rnd,
            #               points, wind, relay_squad]))
            
            results.append(bib +','+ TFFRS_ID +','+ team_name +','+ team_code +','+ \
                        first_name +','+ last_name +','+ gender +','+ year +','+ \
                        date_of_birth +','+ event_code +','+ event_name +','+ \
                        event_division +','+ event_min_age +','+ event_max_age +','+ \
                        sub_event_code +','+ mark +','+ metric +','+ fat +','+ \
                        place +','+ score +','+ heat +','+ heat_place +','+ \
                        rnd +','+ points +','+ wind +','+ relay_squad)

        return Response(results, status.HTTP_200_OK)


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
            table = TimingSession.objects.filter(Q(coach=user.coach)
                        & Q(start_time__range=(start_date, stop_date))).values()
        else:
            table = TimingSession.objects.filter(Q(private='false')
                        & Q(start_time__range=(start_date, stop_date))).values()
        #reset indices for pagination without changing id
    if begin == 0 and stop == 0:
        return Response({'results': table, 'num_sessions': len(table)},
                        status.HTTP_200_OK)
    else:
        i = 1
        result = []
        for instance in table[::-1]:
            if i >= begin and i <= stop:
                #if indices are in the range of pagination, append to return list
                result.append(instance)
            i += 1
        #result = list(reversed(result))
        return Response({'results': result, 'num_sessions': len(table)},
                        status.HTTP_200_OK)


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
    user = request.user

    # Assign the session to a coach.
    c = user.coach

    date = data['race_date']
    datestart = dateutil.parser.parse(date)
    dateover = datestart + timezone.timedelta(days=1)
    # Create the timing session.
    name = data['race_name']
    ts = TimingSession.objects.create(name=name, coach=c, start_time=datestart, stop_time=dateover)

    # Create readers and add to the race.
    for r_id in data['readers']:
        try:
            r = Reader.objects.get(id_str=r_id)
        except ObjectDoesNotExist:
            r = Reader.objects.create(id_str=r_id, coach=c, name=r_id)
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
        runner, created = User.objects.get_or_create(username=username,
                defaults={'first_name':first_name, 'last_name':last_name, 'last_login': timezone.now()})

        a, created = Athlete.objects.get_or_create(user=runner)

        team, created = Team.objects.get_or_create(name=athlete['team'], coach=c, 
        			defaults={'tfrrs_code': athlete['team']})
        # add TFRRS team code here

        today = datetime.date.today()
        a.birth_date = today.replace(year=today.year - int(athlete['age']))
        a.team = team
        a.gender = athlete['gender']
        a.save()

        # Create the rfid tag object and add to session.
        tag_id = athlete['tag']
        try:
            # If the tag already exists in the system, overwrite its user.
            tag = Tag.objects.get(id_str=tag_id)
            tag.athlete = a
            tag.save()
        except ObjectDoesNotExist:
            tag = Tag.objects.create(id_str=tag_id, athlete=a)
        # FIXME: What does this do?

        ts.registered_tags.add(tag.pk)

    return Response({}, status.HTTP_201_CREATED)

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
        return Response({}, status.HTTP_403_FORBIDDEN)

    coach = user.coach
    start_time = dateutil.parser.parse(data['start_time'])
    #stop_time = dateutil.parser.parse(data['start_time'])

    ts = TimingSession(name=data['title'], coach=coach, 
                        start_time=start_time, stop_time=start_time, 
                        track_size=data['track_size'], 
                        interval_distance=data['interval_distance'], 
                        filter_choice=False, private=True)
    
    # set start button time in milliseconds since epoch
    timestamp = (start_time.replace(tzinfo=None)-EPOCH).total_seconds()
    ts.start_button_time = int(round(timestamp * 10**3))
    ts.save()

    results = data['results']
    if results:
        
        reader, created = Reader.objects.get_or_create(id_str='ArchivedReader', 
                defaults={ 'name': 'Archived Reader', 'coach': coach })
        ts.readers.add(reader.pk)

        for runner in results:
            new_user, created = User.objects.get_or_create(
                                    username=runner['username'], defaults={
                                        'first_name': runner['first_name'],
                                        'last_name': runner['last_name'],
                                        'last_login': timezone.now()})
            if created:
                # Register new athlete.
                athlete = Athlete()
                athlete.user = new_user
                athlete.save()

                # add coach's team to new athlete's team
                if coach.team_set.all():
                    team = coach.team_set.all()[0]
                    athlete.team = team
                    athlete.save()

            tags = Tag.objects.filter(athlete=new_user.athlete)
            if tags:
                tag = tags[0]
            else:
                tag = Tag.objects.create(id_str=runner['username'], athlete=athlete)

            # register tag to the timing session
            ts.registered_tags.add(tag.pk)

            # init reference timestamp
            time = ts.start_button_time

            for split in runner['splits']:
                try:
                    #x = timezone.datetime.strptime(split, "%M:%S.%f")
                    mins, secs = split.split(':')
                    diff = int(round((int(mins) * 60 + float(secs)) * 10**3))
                except:
                    diff = int(round(float(secs) * 10**3))

                time += diff

                tt = Split.objects.create(tag_id=tag.id, athlete_id=new_user.athlete.id, time=time, reader_id=reader.id)
                ts.splits.add(tt.pk)

    return Response({}, status=status.HTTP_201_CREATED)

# TODO: Move to TimingSessionViewSet
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
    all_tags = ts.splits.values_list('tag_id', flat=True).distinct()
    tag = Tag.objects.filter(athlete_id=int(data['user_id']), id__in=all_tags)
    dt = int(float(data.get('val', 0)) * 1000)
    
    if data['action'] == 'edit':
        ts._edit_split(tag[0].id, int(data['indx']), dt)
    elif data['action'] == 'insert':
        ts._insert_split(tag[0].id, int(data['indx']), dt, True)
    elif data['action'] == 'delete':
        ts._delete_split(tag[0].id, int(data['indx']))
    elif data['action'] == 'split':
        ts._insert_split(tag[0].id, int(data['indx']), dt, False)
    elif data['action'] == 'total_time':
        ts._overwrite_final_time(tag[0].id, int(data['hour']),
                                 int(data['min']), int(data['sec']),
                                 int(data['mil']))
    else:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    return Response({}, status=status.HTTP_202_ACCEPTED)
    
