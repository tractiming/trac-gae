from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from trac.models import Coach, Athlete, Team, Tag, TimingSession
from trac.serializers import (
    AthleteSerializer, CoachSerializer, RegistrationSerializer
)
from rest_framework import viewsets, permissions, status, views
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import (
    api_view, permission_classes, authentication_classes, detail_route
)
from rest_framework.authentication import BasicAuthentication
from trac.utils.user_util import is_athlete, is_coach, user_type
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from oauth2_provider.models import Application
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout



class CoachViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CoachSerializer
    queryset = Coach.objects.all()


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

        elif is_athlete(user):
            return Athlete.objects.filter(user=user)

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


# FIXME: add to timingsession serializer.
class RegistrationView(views.APIView):
    """
    Registers a user and creates server-side client.
    """
    permission_classes = ()

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data
        # Create the user in the database.
        user = User.objects.create(username=data['username'])
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
                                                       tfrrs_code=team_name)
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
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# DEPRECATE
class verifyLogin(views.APIView):
    permission_classes = ()

    def post(self, request):
        data = request.POST
        #Does the token exist?
        try:
            token = AccessToken.objects.get(token=data['token'])
        except: #ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)

        #Is the Token Valid?
        if token.expires < timezone.now():
            return Response({}, status.HTTP_404_NOT_FOUND)
        else:
            return Response({}, status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes((BasicAuthentication,))
def auth_login(request):
    """
    Log a user into the site. Create Django backend token.
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

''' I think we can remove this.
class userType(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        data = request.GET
        #Is the user in the coaches table?
        user = self.request.user
        try:
            cp = Coach.objects.get(user=user)
        except: #NotCoach:
            try:
                ap = Athlete.objects.get(user=user)
            except: #NotAthlete
                return Response({}, status.HTTP_404_NOT_FOUND)
            return Response("athlete")
        return Response("coach")
'''

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
    result = {'org': user.groups.get(id=1).name,
              'name': user.username,
              'email': email}
    return Response(result, status.HTTP_200_OK)

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
                          last_name=request.POST.get('last_name'))
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
        token = AccessToken(user=u, client=u.oauth2_client.get(user=u),
                            expires=timezone.now()+timezone.timedelta(minutes=5))
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


