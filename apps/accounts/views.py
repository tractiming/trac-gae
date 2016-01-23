import uuid

import requests
from django.conf import settings
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
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

from decimal import Decimal

from djstripe.models import Customer

import stripe

_TOKENINFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'


def _get_user_id(token, client_id):
    """Verify a Google `id_token` and return a user id. See:
    https://developers.google.com/identity/sign-in/web/backend-auth.
    Return None if the token is invalid.
    """
    try:
        id_info = client.verify_id_token(token, client_id)
    except crypt.AppIdentityError:
        return None
    except ValueError:
        # Handle iOS error "ValueError: Plaintext too large".
        response = requests.get(_TOKENINFO_URL, params={'id_token': token})
        if response.status_code != 200:
            return None
        id_info = response.json()

    if any((id_info['aud'] not in [settings.GOOGLE_AUTH_CLIENT_ID,
                                   settings.GOOGLE_AUTH_CLIENT_ID_IOS,
                                   settings.GOOGLE_AUTH_CLIENT_ID_ANDROID],
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

@api_view(['post'])
@permission_classes((permissions.AllowAny,))
def stripeSingleCharge(request):
    """Create a single one-time payment charge for an anonymous user via Stripe.

    Send the stripeID, amount you want to charge them, and user ID if
    applicable.
    """
    stripe.api_key = "sk_test_8dwmRwbSMzZNticzW7fQaKu0"

    # Get the credit card details submitted by the form
    token = request.POST['stripeToken']
    price = request.POST['price']

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
      charge = stripe.Charge.create(
          amount=price, # amount in cents, again
          currency="usd",
          source=token,
          description="TRAC Timing"
      )
    except stripe.error.CardError, e:
      # The card has been declined
      pass

    return Response(201, status.HTTP_201_CREATED)

@api_view(['post'])
@permission_classes((permissions.IsAuthenticated,))
def stripe_CustomerPayment(request):
    """Create a single payment charge for a registered user via Stripe.

    Send the stripeID, amount you want to charge them, and user ID if
    applicable.
    """
    stripe.api_key = "sk_test_8dwmRwbSMzZNticzW7fQaKu0"
    user = request.user
    # Get the credit card details submitted by the form
    price = request.POST['price']

    customer, created = Customer.get_or_create(subscriber=user)

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
      charge = stripe.Charge.create(
          amount=price, # amount in cents, again
          currency="usd",
          description="TRAC Timing",
          customer=customer.id
      )
    except stripe.error.CardError, e:
      # The card has been declined
      pass

    return Response(201, status.HTTP_201_CREATED)

