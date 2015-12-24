import ast
import datetime
import dateutil.parser
import json
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status, pagination, filters
from rest_framework.decorators import api_view, permission_classes, detail_route
from rest_framework.response import Response

from trac.filters import TimingSessionFilter
from trac.models import TimingSession, Reader, Tag, Split, Team, Athlete
from trac.serializers import TimingSessionSerializer
from trac.utils.integrations import tfrrs
from trac.utils.phone_split_util import create_phone_split
from trac.utils.user_util import is_athlete, is_coach


EPOCH = timezone.datetime(1970, 1, 1)


class TimingSessionViewSet(viewsets.ModelViewSet):
    """
    Timing session resource.
    ---
    list:
      parameters:
      - name: start_date
        description: Get sessions after this date
        required: false
        type: str
        paramType: query
      - name: stop_date
        description: Get sessions before this date
        required: false
        type: str
        paramType: query
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TimingSessionFilter

    def get_queryset(self):
        """
        Filter sessions by user.
        """
        user = self.request.user

        # If the user is an athlete, list all the workouts he has run.
        if is_athlete(user):
            return TimingSession.objects.filter(
                splits__athlete=user.athlete).distinct()
        
        # If the user is a coach, list all sessions he manages.
        elif is_coach(user):
            return TimingSession.objects.filter(coach=user.coach)
            
        # If not a user or coach, list all public sessions.
        else:
            return TimingSession.objects.filter(private=False)

    def filter_queryset(self, queryset):
        # Return sessions in reverse chronological order.
        queryset = super(TimingSessionViewSet, self).filter_queryset(queryset)
        return queryset.order_by('-start_time')
    
    @csrf_exempt
    @detail_route(methods=['post'])
    def reset(self, request, *args, **kwargs):
        """
        Reset a timing session by clearing all of its tagtimes.
        ---
        omit_parameters:
        - form
        """
        session = self.get_object()
        session.clear_results()
        return Response({}, status=status.HTTP_202_ACCEPTED)
    
    @csrf_exempt
    @detail_route(methods=['post'])
    def open(self, request, *args, **kwargs):
        """
        Open a session for the next 24 hrs.
        ---
        omit_parameters:
        - form
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
        ---
        omit_parameters:
        - form
        """
        session = self.get_object()
        session.stop_time = timezone.now()
        session.save()
        return Response({}, status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['POST'])
    def start_timer(self, request, *args, **kwargs):
        """
        Start a session, ie, calibrate the gun time.
        ---
        omit_parameters:
        - form
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
        """
        Calculate individual-level results.
        ---
        parameters:
        - name: limit
          description: Maximum number of results to return
          required: false
          type: int
          paramType: query
        - name: offset
          description: Start results set from this offset
          required: false
          type: int
          paramType: query
        - name: all_athletes
          description: >
            If True, return result for all registered athletes,
            regardless of whether or not they have recorded a time
          required: false
          type: boolean
          paramType: query
        - name: gender
          description: Filter by gender
          required: false
          type: string
          paramType: query
        - name: age_lte
          description: Maximum age (inclusive)
          required: false
          type: int
          paramType: query
        - name: age_gte
          description: Minimum age (inclusive)
          required: false
          type: string
          paramType: query
        - name: teams
          description: Get results for these teams only
          required: false
          type: string
          paramType: query
          allowMultiple: true
        """
        to_int = lambda x: int(x) if x is not None else x
        gender = request.query_params.get('gender', None)
        age_lte = to_int(request.query_params.get('age_lte', None))
        age_gte = to_int(request.query_params.get('age_gte', None))
        teams = request.query_params.get('teams', None)
        limit = int(request.query_params.get('limit', 25))
        offset = int(request.query_params.get('offset', 0))
        all_athletes = bool(request.query_params.get('all_athletes', False))

        session = self.get_object()
        raw_results = session.individual_results(limit, offset, gender=gender,
                                                 age_lte=age_lte, age_gte=age_gte,
                                                 teams=teams)
        extra_results = []
        distinct_ids = set(session.splits.values_list('athlete_id',
                                                      flat=True).distinct())
        if (len(raw_results) < limit) and all_athletes:
            # Want to append results set with results for runners who are
            # registered, but do not yet have a time. These results are added
            # to the end of the list, since they cannot be ordered. 
            if len(raw_results) == 0:
                extra_offset = offset - session.num_athletes
            else:
                extra_offset = 0
            extra_limit = limit - len(raw_results)
            additional_athletes = []
            for tag in session.registered_tags.all()[extra_offset:extra_limit]:
                has_split = (session.id in  tag.athlete.split_set.values_list(
                    "timingsession", flat=True).distinct())

                # If the athlete already has at least one split, they will
                # already show up in the results.
                if not has_split:
                    extra_results.append(session.calc_athlete_splits(
                        tag.athlete_id))

                distinct_ids |= set(session.registered_tags.values_list(
                    'athlete_id', flat=True).distinct())

        results = {
            'num_results': len(distinct_ids),
            'num_returned': len(raw_results)+len(extra_results),
            'results': [] 
        }

        for result in (raw_results + extra_results):
            individual_result = {
                'name': result.name,
                'id': result.user_id,
                'splits': [[str(split)] for split in result.splits],
                'total': str(result.total),
                'has_split': result in raw_results 
            }
            results['results'].append(individual_result)

        return Response(results)

    @detail_route(methods=['get'])
    def team_results(self, request, pk=None):
        """
        Calculate team-level results.
        """
        session = self.get_object()
        raw_results = session.team_results()

        results = []
        for place, result in enumerate(raw_results):
            team_result = result
            team_result['place'] = place+1
            results.append(team_result)

        return Response(results)

    @detail_route(methods=['post'], permission_classes=[])
    def add_missed_runner(self, request, pk=None):
        """
        Add a split for a registered tag never picked up by the reader.
        ---
        parameters_strategy: replace
        parameters:
        - name: tag_id
          description: Tag ID
          required: true
          type: int
          paramType: form
        - name: hour
          description: Hour of time
          required: true
          type: int
          paramType: form
        - name: min
          description: Minute of time
          required: true
          type: int
          paramType: form
        - name: sec
          description: Second of time
          required: true
          type: int
          paramType: form
        - name: mil
          description: Millisecond of time
          required: true
          type: int
          paramType: form
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
        session = self.get_object()
        tfrrs_results = tfrss.format_tfrrs_results(session)
        return Response(tfrss_results)


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
        try:
            #look for athletes in a coaches direct roster, and if they aren't found, create a random username
            username = first_name + last_name
            runner = User.objects.get(username=username)
            a = Athlete.objects.get(user=runner)
            team  = Team.objects.get(name=athlete['team'], coach=c)

        except ObjectDoesNotExist:
            username = uuid.uuid4()
            runner, created = User.objects.get_or_create(username=username,
                defaults={'first_name':first_name, 'last_name':last_name, 'last_login': timezone.now()})
            a, created = Athlete.objects.get_or_create(user=runner)
            team, created  = Team.objects.get_or_create(name=athlete['team'], coach=c, defaults={'tfrrs_code': athlete['team']})


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

# TODO: Merge with POST /sessions
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def upload_workouts(request):
    """ 
    Create a complete workout through CSV file upload.
    ---
    parameters:
    - name: title
      description: workout title
      paramType: form
    - name: start_time
      description: start date of workout in ISO string format
      paramType: form
    - name: track_size
      description: size of track
      paramType: form
    - name: interval_distance
      description: distance for each split
      paramType: form
    - name: results
      description: workout results object
      paramType: body
    """
    #- username: athlete username
    #- first_name: athlete first name (used to create new athlete if doesn't exist)
    #- last_name: athlete last name (used to create new athlete if doesn't exist)
    #- splits: list of split times
    #Note: The created workout will be automatically set to filter splits and private.
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
    

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def add_individual_splits(request):
    """
    Add splits from phone for specific individuals. Post Athlete ID and datetime.
    """
    if request.method == 'POST':
        data = request.POST
        split_list = ast.literal_eval(data['s'])
        
        split_status = 0
        for split in split_list:
            if create_phone_split(split[0], split[1]):
                split_status = -1

        if split_status:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=status.HTTP_201_CREATED)
