import ast
import csv
import datetime
import json
import logging
import uuid
from collections import OrderedDict

import dateutil.parser
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mass_mail
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from rest_framework import viewsets, permissions, status, pagination, filters
from rest_framework.decorators import api_view, permission_classes, detail_route
from rest_framework.response import Response

from backends._gcs import gcs_writer, get_public_link
from trac.filters import TimingSessionFilter
from trac.models import TimingSession, Reader, Tag, Split, Team, Athlete
from trac.serializers import TimingSessionSerializer
from trac.utils.integrations import tfrrs
from trac.utils.phone_split_util import create_phone_split
from trac.utils.pdf_util import write_pdf_results
from trac.utils.split_util import format_total_seconds
from trac.utils.user_util import is_athlete, is_coach


log = logging.getLogger(__name__)


EPOCH = timezone.datetime(1970, 1, 1)


class TimingSessionViewSet(viewsets.ModelViewSet):
    """Timing session resource.

    A timing session can be, for example, a workout or a race. It
    collects splits and manages results and athletes. Each session
    is owned by a coach.
    ---
    create:
      omit_parameters:
      - query
    update:
      omit_parameters:
      - query
    retrieve:
      omit_parameters:
      - query
    partial_update:
      omit_parameters:
      - query
    destroy:
      omit_parameters:
      - query
    """
    serializer_class = TimingSessionSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
    filter_class = TimingSessionFilter
    search_fields = ('name',)

    def get_queryset(self):
        """Filter sessions by user.

        If the user is an athlete, list the sessions he has
        completed. If the user is a coach, list the sessions he owns.
        Otherwise, list all public sessions.
        """
        user = self.request.user

        if is_athlete(user):
            return TimingSession.objects.filter(
                splits__athlete=user.athlete).distinct()
        elif is_coach(user):
            return TimingSession.objects.filter(coach=user.coach)
        else:
            return TimingSession.objects.filter(private=False)

    def filter_queryset(self, queryset):
        """Return sessions in reverse chronological order."""
        queryset = super(TimingSessionViewSet, self).filter_queryset(queryset)
        return queryset.order_by('-start_time')

    @csrf_exempt
    @detail_route(methods=['post'],
                  permission_classes=(permissions.IsAuthenticated,))
    def reset(self, request, *args, **kwargs):
        """Reset a timing session by clearing all of its tagtimes.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        """
        session = self.get_object()
        session.clear_results()
        return Response(status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['post'],
                  permission_classes=(permissions.IsAuthenticated,))
    def open(self, request, *args, **kwargs):
        """Open a session for the next 24 hrs.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        """
        session = self.get_object()
        session.start_time = timezone.now() - timezone.timedelta(seconds=8)
        session.stop_time = session.start_time + timezone.timedelta(days=1)
        session.save()
        return Response(status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['post'],
                  permission_classes=(permissions.IsAuthenticated,))
    def close(self, request, *args, **kwargs):
        """Close a session by setting its stop time to now.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        """
        session = self.get_object()
        session.stop_time = timezone.now()
        session.save()
        return Response(status=status.HTTP_202_ACCEPTED)

    @csrf_exempt
    @detail_route(methods=['post'],
                  permission_classes=(permissions.IsAuthenticated,))
    def start_timer(self, request, *args, **kwargs):
        """Start a session, i.e., calibrate the gun time.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        """
        # FIXME: This is a hack that offsets the delay the reader has in
        # setting its real time.  Also note that the start time is taken to be
        # the time the request hits the server, not the time the button is
        # pressed on the phone, etc.
        current_time = datetime.datetime.utcnow()-datetime.timedelta(seconds=8)
        timestamp = int((current_time - timezone.datetime(
            1970, 1, 1)).total_seconds()*1000)

        session = self.get_object()
        session.start_button_time = timestamp
        session.save()
        return Response(status=status.HTTP_202_ACCEPTED)

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
            description: Filter by gender ("M" or "F")
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
        omit_parameters:
          - form
        parameters_strategy:
          query: replace
        omit_serializer: true
        type:
          name:
            description: Athlete's name
            required: true
            type: string
          id:
            description: Athlete id
            required: true
            type: int
          splits:
            description: Array of splits for this athlete
            required: true
            type: list
          total:
            description: Cumulative time for this athlete
            required: true
            type: string
          has_split:
            description: Whether or not the athlete has recorded a time
            required: true
            type: boolean
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
            for athlete in session.registered_athletes.all(
                    )[extra_offset:extra_limit]:
                has_split = (session.id in athlete.split_set.values_list(
                    "timingsession", flat=True).distinct())

                # If the athlete already has at least one split, they will
                # already show up in the results.
                if not has_split:
                    extra_results.append(session._calc_athlete_splits(
                        athlete.id))

                distinct_ids |= set(session.registered_athletes.values_list(
                    'id', flat=True).distinct())

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
        """Calculate team-level results.
        ---
        omit_serializer: true
        omit_parameters:
          - form
          - query
        omit_serializer: true
        type:
          athletes:
            description: Athlete IDs of scoring runners
            required: true
            type: list
          score:
            description: Point total
            required: true
            type: int
          id:
            description: Team ID
            required: true
            type: int
          name:
            description: Team name
            required: true
            type: string
          place:
            description: Place taken by this team in this session
            required: true
            type: int
        """
        session = self.get_object()
        raw_results = session.team_results()

        results = []
        for place, result in enumerate(raw_results):
            team_result = result
            team_result['place'] = place+1
            results.append(team_result)

        return Response(results)

    @detail_route(methods=['post'])
    def upload_results(self, request, pk=None):
        """
        Upload results to an existing workout. Request body should
        be a list of dicts containing athlete id and list of splits.
        If athlete already has results in a workout, overwrite those
        splits. If not, simply append results to existing results.

        TODO: validate coach can save times for the given
        athlete ids.
        TODO: Take file uploads instead of JSON
        ---
        omit_serializer: true
        omit_parameters:
          - query
        parameters_strategy:
          form: replace
        parameters:
        - name: id
          description: Athlete ID
          paramType: form
          type: int
        - name: splits
          description: List of splits (in seconds)
          type: list
          paramType: form
        """
        data = json.loads(request.body)
        session = self.get_object()

        for athlete_data in data:
            try:
                athlete = Athlete.objects.get(pk=int(athlete_data['id']))
            except (ValueError, ObjectDoesNotExist):
                # May fail to convert to int or find athlete.
                return Response('Could not find athlete matching id '
                                '{}'.format(athlete_data['id']),
                                status=status.HTTP_400_BAD_REQUEST)

            Split.objects.filter(timingsession=session,
                                 athlete=athlete).delete()

            splits = athlete_data['splits']
            time = session.start_button_time or 0
            if session.start_button_time is None:
                splits.insert(0, 0)

            for split in splits:
                time += split*1000
                new_split = Split.objects.create(athlete=athlete, time=time)
                session.splits.add(new_split.pk)

        session.save()
        return Response(status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def register_athletes(self, request, pk=None):
        """Append athletes to the list of registered athletes.

        Has no effect if athlete is already registered.
        ---
        omit_parameters:
          - query
        parameters_strategy:
          form: replace
        omit_serializer: true
        parameters:
        - name: athletes
          description: List of athlete IDs
          paramType: form
          type: list
        """
        session = self.get_object()
        new_athletes = set(request.data.pop('athletes', []))
        existing_athletes = set(session.registered_athletes.values_list(
            'id', flat=True))
        request.data.clear()  # Don't allow for updating other fields.
        request.data['registered_athletes'] = list(
            new_athletes | existing_athletes)
        return self.partial_update(request)

    @detail_route(methods=['post'])
    def remove_athletes(self, request, pk=None):
        """Remove athletes from the list of registered athletes.

        If they are not on the list, no effect.
        ---
        omit_parameters:
          - query
        parameters_strategy:
          form: replace
        omit_serializer: true
        parameters:
        - name: athletes
          description: List of athlete IDs
          paramType: form
          type: list
        """
        session = self.get_object()
        athletes_to_remove = set(request.data.pop('athletes',[]))
        existing_athletes = set(session.registered_athletes.values_list(
            'id', flat=True))
        request.data.clear()
        request.data['registered_athletes'] = list(x for x in existing_athletes if
            x not in athletes_to_remove)
        return self.partial_update(request)

    @detail_route(methods=['post'])
    def export_results(self, request, pk=None):
        """Get a link to a text results file.

        The file will be formatted as a CSV with one column for name
        and one for total time. NOTE: This creates a public link to
        the results. Anyone with this link will be able to download
        the file.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        parameters_strategy:
          form: replace
        parameters:
        - name: file_format
          description: Type of file to write ("csv", "pdf", or "tfrss")
        type:
          uri:
            required: true
            type: url
            description: Link to downloadable results file
        """
        session = self.get_object()

        file_format = request.data.get('file_format', 'csv')
        if file_format not in ('csv', 'pdf', 'tfrrs'):
            return Response('Invalid file format',
                            status=status.HTTP_400_BAD_REQUEST)

        extension = 'pdf' if file_format == 'pdf' else 'csv'
        tfrrs_name = '-tfrrs' if file_format == 'tfrrs' else ''
        storage_path = '/'.join((settings.GCS_RESULTS_DIR,
                                 str(session.pk),
                                 'individual{tfrrs}.{extension}'.format(
                                     extension=extension,
                                     tfrrs=tfrrs_name)))

        if file_format == 'tfrrs':
            results_to_write = tfrrs.format_tfrrs_results(session)
            header = tfrrs._TFRRS_FIELDS
        else:
            results_to_write = (OrderedDict((
                ('name', result.name),
                ('time', format_total_seconds(result.total)))
            ) for result in session.individual_results())
            header = ('Name', 'Time')

        with gcs_writer(settings.GCS_RESULTS_BUCKET, storage_path,
                        make_public=True) as _results:
            if file_format in ('csv', 'tfrrs'):
                writer = csv.writer(_results)
                writer.writerow(header)
                for result in results_to_write:
                    writer.writerow(result.values())
            elif file_format == 'pdf':
                write_pdf_results(_results, results_to_write)

        log.debug('Saved results to %s', storage_path)

        return Response({'uri': get_public_link(settings.GCS_RESULTS_BUCKET,
                                                storage_path)})

    @detail_route(methods=['post'],
                  permission_classes=(permissions.IsAuthenticated,))
    def email_results(self, request, pk=None):
        """Email all users in a workout with attachment link of workout.

        Will attach a CSV file to an email at all users that have an email
        associated with them. If they do not have an email, it will not
        include them.
        """
        session = self.get_object()
        athletes = Athlete.objects.filter(
            Q(split__timingsession=session) & ~Q(user__email='')).distinct()
        full_results = (request.POST.get('full_results', 1) in
                        ('true', 'True', 1))

        email_template = '../templates/email_templates/{}'.format(
            'results_email.txt' if full_results else
            'results_email_single.txt')
        if full_results:
            resp = self.export_results(request)
            if resp.status_code != 200:
                return Response(status=status.HTTP_404_BAD_REQUEST)
            download_link = resp.data['uri']
        else:
            download_link = None

        email_list = []
        for athlete in athletes:
            athlete_email = athlete.user.email
            context = {
                'name': athlete.user.first_name,
                'date': session.start_time
            }
            if full_results:
                context.update({'link': download_link})
            else:
                context.update({
                    'workout_name': session.name,
                    'splits': session._calc_athlete_splits(athlete.id).splits
                })
            message = (
                session.name,
                loader.render_to_string(email_template, context),
                'tracchicago@gmail.com',
                [athlete_email]
            )
            email_list.append(message)

        send_mass_mail(email_list, fail_silently=False)
        return Response(status=status.HTTP_200_OK)


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

        ts.registered_athletes.add(tag.athlete.pk)

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

            # register tag to the timing session
            ts.registered_athletes.add(new_user.athlete.pk)

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

                tt = Split.objects.create(athlete_id=new_user.athlete.id,
                                          time=time,
                                          reader_id=reader.id)
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
    athlete = Athlete.objects.get(id=int(data['user_id']))
    dt = int(float(data.get('val', 0)) * 1000)

    if data['action'] == 'edit':
        ts._edit_split(athlete.id, int(data['indx']), dt)
    elif data['action'] == 'insert':
        ts._insert_split(athlete.id, int(data['indx']), dt, True)
    elif data['action'] == 'delete':
        ts._delete_split(athlete.id, int(data['indx']))
    elif data['action'] == 'split':
        ts._insert_split(athlete.id, int(data['indx']), dt, False)
    elif data['action'] == 'total_time':
        ts._overwrite_final_time(athlete.id, int(data['hour']),
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
