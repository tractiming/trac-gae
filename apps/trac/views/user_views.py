import base64
import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token
from rest_framework import (
    viewsets, permissions, status, pagination, filters
)
from rest_framework.decorators import permission_classes, detail_route
from rest_framework.response import Response

from trac.filters import AthleteFilter, CoachFilter
from trac.models import Coach, Athlete, Tag, TimingSession
from trac.serializers import (
    AthleteSerializer, CoachSerializer, UserSerializer
)
from trac.utils.user_util import is_athlete, is_coach


class UserViewSet(viewsets.ModelViewSet):
    """
    User resource.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get_object(self):
        """Alias 'me' to the current user."""
        if self.kwargs.get('pk', None) == 'me':
            return self.request.user
        else:
            return super(UserViewSet, self).get_object()

    @detail_route(methods=['post'])
    def change_password(self, request, *args, **kwargs):
        """
        Change a user's password.
        """
        user = self.get_object()
        old_password = request.data.get('old_password')
        if not user.check_password(old_password):
            return Response(status=status.HTTP_403_FORBIDDEN)
        user.set_password(request.data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def tutorial_limiter(self, request, *args, **kwargs):
        user = request.user
        show_tutorial = (timezone.now() - user.date_joined
                            < datetime.timedelta(60))
        return Response({'show_tutorial': show_tutorial},
                        status=status.HTTP_200_OK)


class CoachViewSet(viewsets.ModelViewSet):
    """Coach resource.

    A coach manages teams, sessions, and athletes.
    ---
    create:
      omit_parameters:
      - query
    update:
      omit_parameters:
      - query
    partial_update:
      omit_parameters:
      - query
    destroy:
      omit_parameters:
      - query
    retrieve:
      omit_parameters:
      - query
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CoachSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CoachFilter

    def get_queryset(self):
        return Coach.objects.filter(user__id=self.request.user.pk)


class AthleteViewSet(viewsets.ModelViewSet):
    """Athlete resource.

    An athlete competes in sessions, appears in results, may
    belong to a team, and can be assigned a tag ("bib").
    ---
    create:
      omit_parameters:
      - query
    update:
      omit_parameters:
      - query
    partial_update:
      omit_parameters:
      - query
    destroy:
      omit_parameters:
      - query
    retrieve:
      omit_parameters:
      - query
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = AthleteSerializer
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
    filter_class = AthleteFilter
    search_fields = ('user__first_name', 'user__last_name', 'team__name')

    def get_queryset(self):
        """
        Get athletes associated with a coach.
        """
        user = self.request.user

        if is_coach(user):
            coach = Coach.objects.get(user=user)
            return Athlete.objects.filter(team__in=coach.team_set.all())

        elif is_athlete(user):
            return Athlete.objects.filter(user=user)

        else:
            return Athlete.objects.filter(split__timingsession__private=False).distinct()

    def create(self, request, *args, **kwargs):
        # We want to allow for a tag to be created at the same time as an
        # Athlete. However, creating a new tag requires us to specify an
        # athlete. Here, we remove the tag from the request, create the
        # athlete, and then create the tag if needed.
        tag_str = request.data.pop('tag', None)
        if tag_str is not None:
            if not tag_str or Tag.objects.filter(id_str=tag_str).exists():
                return Response({'tag': ['Invalid id']},
                                status=status.HTTP_400_BAD_REQUEST)
        resp = super(AthleteViewSet, self).create(request, *args, **kwargs)
        if tag_str:
            athlete = Athlete.objects.get(pk=resp.data['id'])
            tag = Tag.objects.create(athlete=athlete, id_str=tag_str)
            resp.data['tag'] = tag.id_str
        return resp

    def update(self, request, *args, **kwargs):
        # Similar to `create`, we want to allow for editing a tag through
        # editing an athlete.
        athlete = self.get_object()

        if 'tag' in request.data:
            tag_str = request.data.pop('tag')

            # If tag is given, but listed as null, delete the tag.
            if not tag_str:
                Tag.objects.filter(athlete=athlete).delete()

            else:
                if Tag.objects.filter(id_str=tag_str).exists():
                    # If tag exists and belongs to current user, do nothing.
                    if Tag.objects.get(id_str=tag_str).athlete == athlete:
                        pass
                    # If tag exists and does not belong to current user, raise
                    # validation error.
                    else:
                        return Response({'tag': ['Invalid ID']},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    # If tag does not exist, create it, deleting any existing
                    # tags.
                    Tag.objects.filter(athlete=athlete).delete()
                    Tag.objects.create(athlete=athlete, id_str=tag_str)

        return super(AthleteViewSet, self).update(request, *args, **kwargs)

    @detail_route(methods=['get'])
    def completed_sessions(self, request, *args, **kwargs):
        """Get the results of one athlete across all sessions.
        ---
        omit_serializer: true
        omit_parameters:
        - query
        - form
        type:
          id:
            description: Session ID
            type: integer
          name:
            description: Athlete name
            type: string
          date:
            description: Date of the session
            type: string
          splits:
            description: Times the athlete has recorded in this session
            type: list
          total:
            description: Cumulative time for the athlete in this session
            type: string
        """
        athlete = self.get_object()
        name = athlete.user.get_full_name() or athlete.user.username

        sessions = TimingSession.objects.filter(
            splits__athlete_id=athlete.id).distinct()
        results = {
            'name': name,
            'sessions': []
        }

        # Iterate through each session to get all of a single users workouts
        for session in sessions:
            session_results = session._calc_athlete_splits(athlete.id)
            session_info = {
                'id': session.id,
                'name': session.name,
                'date': session.start_time,
                'splits': session_results.splits,
                'total': session_results.total
            }
            results['sessions'].append(session_info)

        return Response(results)
        

@csrf_exempt
@permission_classes((permissions.AllowAny,))
def send_email(request):
    """
    Send an email related to a user password reset.
    TODO: move to /users; fix HttpResponse
    ---
    parameters:
    - name: email
      paramType: form
    - name: user
      paramType: form
    """
    email = request.POST.get('email')
    name = request.POST.get('user')
    user = User.objects.get(username=name)
    if user.email != email:
        return HttpResponse(status.HTTP_403_FORBIDDEN)

    uidb64 = base64.urlsafe_b64encode(force_bytes(user.pk))
    token = AccessToken(user=user,
                        application = Application.objects.get(client_id='aHD4NUa4IRjA1OrPD2kJLXyz34c06Bi5eVX8O94p'),
                        expires=timezone.now()+timezone.timedelta(minutes=5),
                        token=generate_token())
    token.save()
    email_config = {
        'email': email,
        'domain': request.META['HTTP_HOST'],
        'site_name': 'TRAC',
        'uid': uidb64,
        'user': user,
        'token': str(token),
        'protocol': 'https://',
    }
    url = "/".join((email_config['domain'], 'UserSettings',
                    email_config['uid'], email_config['token'], ''))
    email_body = loader.render_to_string('../templates/email_templates/email_template.html',
                                         email_config)
    send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com',
              (email_config['email'],), fail_silently=False)
    return HttpResponse(status.HTTP_200_OK)


@csrf_exempt
@permission_classes((permissions.AllowAny,))
def request_quote(request):
    """
    If user requests quote, have it email founders to proceed from there.
    """
    email = request.POST.get('email')
    name = request.POST.get('name')
    tag_number = request.POST.get('tag_number')
    tag_type = request.POST.get('tag_type')
    system_number = request.POST.get('systems')
    date = request.POST.get('date')
    price = request.POST.get('price')
    context = {'name': name, 'tag_number': tag_number,'tag_type':tag_type,
        'system_number': system_number,'date':date,'price':price}
    send_mail(
        'Quote',
        loader.render_to_string('../templates/email_templates/quote.txt', context),
        'tracchicago@gmail.com',
        [email, 'founders@tracchicago.com'],
        fail_silently=False)
    return HttpResponse(status.HTTP_200_OK)


@csrf_exempt
@permission_classes((permissions.AllowAny,))
def give_athlete_password(request):
    """
    Endpoint to email athletes via the settings page. 

    Will first save any changes made to the athlete's info
    then email them with a link to reset and gain access to
    their account. 
    """
    atl = Athlete.objects.get(id=request.POST.get('id'))
    atl.user.first_name = request.POST.get('first_name')
    atl.user.last_name = request.POST.get('last_name')
    atl.user.email = request.POST.get('email')
    atl.user.save()
    try:  #if tag exists update user. Or create tag.
        tag = Tag.objects.get(id_str = request.POST.get('id_str'))
        tag.athlete = atl
        tag.save()
    except ObjectDoesNotExist:
        try:
            tag = Tag.objects.get(athlete = atl)
            tag.id_str = request.POST.get('id_str')
            tag.save()
        except ObjectDoesNotExist:
            tag = Tag.objects.create(id_str=request.POST.get('id_str'), athlete=atl)

    if atl:
        uidb64 = base64.urlsafe_b64encode(force_bytes(atl.user.pk))
        token = AccessToken.objects.create(user = atl.user, 
            application = Application.objects.get(client_id='aHD4NUa4IRjA1OrPD2kJLXyz34c06Bi5eVX8O94p'), 
            expires = timezone.now()+timezone.timedelta(minutes=2880), 
            token=generate_token())
        token.save()
        c = {
            'name': atl.user.first_name,
            'email': atl.user.email,
            'domain': request.META['HTTP_HOST'],
            'site_name': 'TRAC',
            'uid': uidb64,
            'user': atl.user,
            'username': atl.user.username,
            'token': str(token),
            'protocol': 'https://',
        }
        url = c['domain'] + '/UserSettings/' + c['uid'] + '/' + c['token'] + '/'
        email_body = loader.render_to_string('../templates/email_templates/athlete_password.html', c)
        send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com', [c['email'],], fail_silently=False)
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)

@csrf_exempt
@permission_classes((permissions.AllowAny))
def tag_id_change_athlete(request):
    """
    Endpoint that allows user to change user first and last name.

    Can optionally change the username and password if they choose.
    """
    tag = Tag.objects.get(id_str=request.POST.get('tag_id'))
    ath = tag.athlete
    if not ath.user.password:
        ath.user.first_name = request.POST.get('first_name')
        ath.user.last_name = request.POST.get('last_name')
        ath.user.username = request.POST.get('username')
        ath.user.password = request.POST.get('password')
        return HttpResponse(status.HTTP_201_CREATED)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)