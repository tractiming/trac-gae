import json

from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from oauth2_provider.models import Application, AccessToken
from oauth2_provider.views import TokenView as _TokenView
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from trac.models import User, Team
from trac.serializers import AthleteSerializer, CoachSerializer, UserSerializer
from trac.utils.user_util import user_type, is_coach


_serializer_lookup = {'athlete': AthleteSerializer, 'coach': CoachSerializer}


def create_user(user_info, user_type):
    """Create a new user (Athlete or Coach)."""
    assert user_type in ('athlete', 'coach'), 'Invalid user type'
    serializer_class = _serializer_lookup[user_type]
    serializer = serializer_class(data=user_info)
    serializer.is_valid(raise_exception=True)
    return serializer.create(serializer.validated_data)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def register(request):
    """Register a new coach or athlete."""
    team_name = request.data.pop('organization', None)
    utype = request.data.get('user_type')
    if utype not in ('athlete', 'coach'):
        return Response({'errors': ['Invalid user type']},
                        status=status.HTTP_400_BAD_REQUEST)

    new_user = create_user(request.data, utype)
    if team_name is not None and is_coach(new_user.user):
        Team.objects.create(name=team_name,
                            coach=new_user,
                            primary_team=True)

    # Send email about app availability after sign up.
    context = {}
    send_mail(
        'TRAC Update',
        loader.render_to_string('../templates/noAppAlert.txt', context),
        'tracchicago@gmail.com',
        [request.data['email']],
        fail_silently=False)

    return Response(_serializer_lookup[utype](new_user).data,
                    status=status.HTTP_201_CREATED)


class TokenView(_TokenView):
    """Override the built-in `oauth2_provider` class to avoid
    problems with the `method_decorator` decorator on `post`.
    See `oauth2_provider/views/base.py`.
    """
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        response = HttpResponse(content=body, status=status)

        for k, v in headers.items():
            response[k] = v
        return response


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def login(request):
    """
    Log a user into the site.

    Exchanges a client id, username, and password for a short-lived
    access token. Also returns info about the current user.
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
    resp = TokenView.as_view()(request)
    data = json.loads(resp.content)
    data.pop('refresh_token', None)  # Do not pass back refresh token
    if resp.status_code == 200:
        user = User.objects.get(username=request.data['username'])
        data['user'] = UserSerializer().to_representation(user)
    return Response(data, status=resp.status_code)


@api_view(['get'])
@permission_classes((permissions.AllowAny,))
def verify_login(request):
    """Validate an existing access token.

    If token is valid, return 200, otherwise return 404.
    ---
    parameters:
    - name: token
      description: OAuth2 token
      required: true
      type: string
      paramType: query
    """
    token = request.GET.get('token', '')
    if get_object_or_404(AccessToken, token=token).is_valid():
        return Response(200, status=status.HTTP_200_OK)
    return Response(404, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
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
