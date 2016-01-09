import uuid

from django.conf import settings
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone
from oauth2_provider.models import Application, AccessToken
from oauth2client import client, crypt
from oauthlib.common import generate_token
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models import GoogleSignIn
from trac.serializers import UserSerializer
from trac.views.auth_views import create_user


def _get_user_id(token, client_id):
    """Verify a Google `id_token` and return a user id. See:
    https://developers.google.com/identity/sign-in/web/backend-auth.
    Return None if the token is invalid.
    """
    try:
        id_info = client.verify_id_token(token, client_id)
    except crypt.AppIdentityError:
        return None

    if any((id_info['aud'] not in [settings.GOOGLE_AUTH_CLIENT_ID],
            id_info['iss'] not in settings.GOOGLE_AUTH_DOMAINS)):
        return None

    return id_info['sub']


@api_view(['post'])
@permission_classes((permissions.AllowAny,))
def google_auth(request):
    """Authenticate/login a user given a Google `id_token`.

    If the request is made with a valid Bearer token for a logged in
    user, the Google account will be associated with that user.
    Otherwise, try to retrieve credentials based on the `id_token`,
    creating a new account if needed.
    """
    token = request.data.pop('id_token', None)
    google_client_id = request.data.pop('google_client_id', None)
    trac_client_id = request.data.pop('trac_client_id', None)
    google_id = _get_user_id(token, google_client_id)

    if google_id is None:
        return Response({'errors': ['Invalid Google token']},
                        status=status.HTTP_400_BAD_REQUEST)

    created = False
    try:
        user = GoogleSignIn.objects.get(google_id=google_id).user
        print 'existing user found'
    except ObjectDoesNotExist:
        user = request.user
        if user.is_anonymous():
            # User not logged in - create an account using Google
            # credentials.
            user_info = {
                'username': uuid.uuid4().hex[:30],
                'email': request.data.pop('email', None)
            }
            user = create_user(user_info, 'coach').user
            created = True
            print 'new user created'

        # Existing user - link account to Google
        GoogleSignIn.objects.create(user=user, google_id=google_id)

    app = get_object_or_404(Application, client_id=trac_client_id)
    AccessToken.objects.filter(application=app, user=user).delete()

    raw_token = generate_token()
    expiration = timezone.now() + timezone.timedelta(seconds=36000)
    bearer_token = AccessToken.objects.create(
        user=user, application=app, token=raw_token,
        expires=expiration)

    token_data = {
        'expires_in': 36000,
        'access_token': bearer_token.token,
        'token_type': 'Bearer',
        'scope': bearer_token.scope,
        'user': UserSerializer().to_representation(user)
    }
    resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(token_data, status=resp_status)
