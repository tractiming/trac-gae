import base64
import datetime

from django.conf import settings
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from djstripe.models import Customer
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token
import stripe

from rest_framework import viewsets, permissions, status, views
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    api_view, permission_classes, authentication_classes, detail_route
)
from rest_framework.response import Response

from trac.models import Coach, Athlete, Team, Tag, TimingSession
from trac.serializers import (
    AthleteSerializer, CoachSerializer, RegistrationSerializer, UserSerializer
)
from trac.utils.user_util import is_athlete, is_coach, user_type


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
            return User.objects.get(pk=int(self.kwargs['pk']))

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
    """
    Coach resource.
    """
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CoachSerializer
    queryset = Coach.objects.all()


class AthleteViewSet(viewsets.ModelViewSet):
    """
    Athlete resource.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AthleteSerializer

    def get_queryset(self):
        """
        Get athletes associated with a coach.
        """
        user = self.request.user

        session = self.request.query_params.get('session', None)
        session_filter = Q()
        if session is not None:
            session = get_object_or_404(TimingSession, pk=int(session))
            athletes = session.splits.values_list('athlete_id', flat=True)
            session_filter &= Q(id__in=athletes)

        if is_coach(user):
            coach = Coach.objects.get(user=user)
            athlete_filter = (Q(team__in=coach.team_set.all(),
                                team__primary_team=True) &
                              session_filter)
            return Athlete.objects.filter(athlete_filter)

        elif is_athlete(user):
            return Athlete.objects.filter(Q(user=user) & session_filter)

        else:
            return Athlete.objects.none()
    
    @detail_route(methods=['get'])
    def completed_sessions(self, request, *args, **kwargs):
        """
        Get all the sessions an athlete has participated in.
        """
        athlete = self.get_object()

        # Get the user's name.
        name = athlete.user.get_full_name()
        if not name:
            name = athlete.user.username

        sessions = [session for session in TimingSession.objects.all()
                    if athlete.id in session.splits.values_list('athlete_id',
                        flat=True).distinct()]
        results = {'name': name,
                   'sessions': []} 

        #Iterate through each session to get all of a single users workouts
        for session in sessions:
            session_results = session.calc_athlete_splits(athlete.id)
            session_info = {'id': session.id,
                            'name': session.name,
                            'date': session.start_time,
                            'splits': session_results[3],
                            'total': session_results[4]
                            }
            results['sessions'].append(session_info)

        return Response(results)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def RegistrationView(request):
    """
    Register a new coach or athlete.
    ---
    parameters:
    - name: username
      description: Unique username
      required: true
      type: string
      paramType: form
    - name: password
      description: User's password
      required: true
      type: string
      paramType: form
    - name: email
      description: User's email
      required: true
      type: string
      paramType: form
    - name: user_type
      description: Athlete or coach
      required: true
      type: string
      paramType: form
    - name: organization
      description: Name of the organization to which this user belongs
      required: true
      type: string
      paramType: form
    """
    serializer = RegistrationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)
    data = serializer.data
    # Create the user in the database.
    user = User.objects.create(username=data['username'],
                               last_login=timezone.now())
    user.set_password(data['password'])
    user.email = request.data['email']
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
        team_name = data['organization']
        team, created = Team.objects.get_or_create(name=team_name,
                                                   coach=coach,
                                                   tfrrs_code=team_name, primary_team=True)
        if created:
            team.coach = coach 
            team.save()

        #Creates the Default table for coaches when they register.
        #cp = Coach.objects.get(user=user)
        # Not sure this is the best place for this.
        #for i in range(0, len(DEFAULT_DISTANCES)):
        #    r = PerformanceRecord.objects.create(
        #            distance=DEFAULT_DISTANCES[i], time=DEFAULT_TIMES[i])
        #    cp.performancerecord_set.add(r)
    
    email = user.email
    context = {}
    send_mail('TRAC Update', loader.render_to_string('../templates/noAppAlert.txt',context), 'tracchicago@gmail.com', [email], fail_silently=False)
    return HttpResponse(status.HTTP_200_OK)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

class verifyLogin(views.APIView):
    """
    Verify that a user is currently logged into the site.
    """
    permission_classes = ()

    @csrf_exempt
    def get(self,request):
        """
        Check login status.
        ---
        parameters:
        - name: token
          description: OAuth2 token
          required: true
          type: string
          paramType: query
        """

        data = request.GET.get('token')
        #Does the token exist?
        try:
            token = AccessToken.objects.get(token=data)
        except: #ObjectDoesNotExist:
            return Response(404, status.HTTP_404_NOT_FOUND)

        #Is the Token Valid?
        if token.expires < timezone.now():
            return Response(404, status.HTTP_404_NOT_FOUND)
        else:
            return Response(200, status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes((BasicAuthentication,))
def auth_login(request):
    """
    Log a user into the site. Create Django backend token.
    ---
    parameters:
    - name: username
      description: Username
      required: true
      type: string
      paramType: form
    - name: password
      description: Password
      required: true
      type: string
      paramType: form
    """
    application = Application.objects.get(user=request.user) 
    credentials = {'username': request.user.username,
                   'client_id': application.client_id,
                   'client_secret': application.client_secret,
                   'user_type': user_type(request.user)
                   }
	
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    login(request,user)
    return Response(credentials)

@api_view(['POST'])
def logout(request):
    """
    Logout a user into the site; delete django backend token.
    TODO: Fix broken pipe
    """
    auth_logout(request)


# TODO: Move to AthleteViewSet
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def edit_athletes(request):
    """
    Update and remove athlete profiles from coach.athletes.all() but keeps the
    athlete's user account.
    """
    i_user = request.user
    if not is_coach(i_user):
        return Response({}, status.HTTP_403_FORBIDDEN)
    else:
        # Removes the link with coach account
        if request.POST.get('submethod') == 'Delete':
            #cp = Coach.objects.get(user = i_user) #deletes entire user
            atl = Athlete.objects.get(id=request.POST.get('id'))
            atl.delete()
        
        #Change user's first and last names. Not change username.
        elif request.POST.get('submethod') == 'Update':
            cp = Coach.objects.get(user = i_user)
            atl = Athlete.objects.get(id=request.POST.get('id'))
            atl.user.first_name = request.POST.get('first_name')
            atl.user.last_name = request.POST.get('last_name')
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
                    tag = Tag.objects.create(id_str=request.POST.get('id_str'),
                                             athlete=atl)
            return Response({}, status.HTTP_200_OK)

        elif request.POST.get('submethod') == 'Create':
            cp = Coach.objects.get(user = i_user)
            user, _ = User.objects.get_or_create(
                          username=request.POST.get('username'),
                          first_name=request.POST.get('first_name'),
                          last_name=request.POST.get('last_name'),last_login=timezone.now())
            atl, created = Athlete.objects.get_or_create(user = user)
            atl.team = cp.team_set.all()[0]

            try:
                tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                tag.athlete = atl
            except ObjectDoesNotExist:
                tag = Tag.objects.create(athlete=atl,
                                         id_str=request.POST.get('id_str'))

            tag.save()
            atl.save()
            user.save()

        return Response({}, status.HTTP_200_OK)

@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def token_validation(request):
    """
    Validate a token.
    """
    return HttpResponse(status.HTTP_200_OK)

# TODO: move to /users
@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def reset_password(request):
    """
    Reset a user's password.
    ---
    parameters:
    - name: user
      description: username
      paramType: form
      required: true
      type: string
    - name: password
      description: New password
      paramType: form
      required: true
      type: string
    """
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
                        application=Application.objects.get(user=user),
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
    email_body = loader.render_to_string('../templates/email_template.html',
                                         email_config)
    send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com',
              (email_config['email'],), fail_silently=False)
    return HttpResponse(status.HTTP_200_OK)

@csrf_exempt
@permission_classes((permissions.AllowAny,))
def give_athlete_password(request):
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
    email = request.POST.get('email')
    name = request.POST.get('username')
    u = User.objects.get(email = email)
    user2 = User.objects.get(username = name)
    if u == user2:
        uidb64 = base64.urlsafe_b64encode(force_bytes(u.pk))
        token = AccessToken.objects.create(user = user2, application = Application.objects.get(user = user2), expires = timezone.now()+timezone.timedelta(minutes=2880), token=generate_token())
        token.save()
        c = {
            'email': email,
            'domain': request.META['HTTP_HOST'],
            'site_name': 'TRAC',
            'uid': uidb64,
            'user': u,
            'username':name,
            'token': str(token),
            'protocol': 'https://',
        }
        url = c['domain'] + '/UserSettings/' + c['uid'] + '/' + c['token'] + '/'
        email_body = loader.render_to_string('../templates/athlete_password.html', c)
        send_mail('Reset Password Request', email_body, 'tracchicago@gmail.com', [c['email'],], fail_silently=False)
        return HttpResponse(status.HTTP_200_OK)
    else:
        return HttpResponse(status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@login_required()
@permission_classes((permissions.IsAuthenticated,))
def reset_password(request):
    name =  base64.urlsafe_b64decode(request.POST.get('user').encode('utf-8'))
    user = get_object_or_404(User, pk=name)
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
    user.accesstoken_set.get(token=token).delete()
    return HttpResponse(status.HTTP_200_OK)


def subscribe(request, **kwargs):
	data = request.POST
	print data
	user = request.user
	print user
	try:
		customer = user.customer
	except:
		customer = Customer.create(user)
	print request.POST.get('stripe_token')
	customer.update_card(request.POST.get('stripe_token'))
	customer.subscribe('monthly')
	
	stripe.api_key = settings.STRIPE_SECRET_KEY
	
	return redirect('/payments')

