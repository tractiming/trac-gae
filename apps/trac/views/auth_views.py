from django.contrib import auth
from django.core.mail import send_mail
from django.template import RequestContext, loader
from oauth2_provider.models import Application
from rest_framework import permissions, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    api_view, permission_classes, authentication_classes, detail_route
)
from rest_framework.response import Response

from trac.serializers import AthleteSerializer, CoachSerializer, UserSerializer
from trac.utils.user_util import user_type


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def register(request):
    """Register a new coach or athlete."""
    utype = request.data.get('user_type')

    if utype == 'athlete':
        serializer_class = AthleteSerializer
    elif utype == 'coach':
        serializer_class = CoachSerializer
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_user = serializer.create(serializer.validated_data)

    # Send email about app availability after sign up.
    context = {}
    send_mail(
        'TRAC Update',
        loader.render_to_string('../templates/noAppAlert.txt', context),
        'tracchicago@gmail.com',
        [request.data['email']],
        fail_silently=False)

    return Response(serializer_class(new_user).data,
                    status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes((BasicAuthentication,))
def login(request):
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
    credentials = {
        'client_id': application.client_id,
        'client_secret': application.client_secret,
        'user': UserSerializer().to_representation(request.user)
    }
	
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = auth.authenticate(username=username, password=password)
    auth.login(request, user)
    return Response(credentials)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def logout(request):
    """
    Logout a user into the site; delete django backend token.
    TODO: Fix broken pipe
    """
    auth.logout(request)
    return Response(status=status.HTTP_200_OK)


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

