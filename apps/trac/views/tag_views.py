from trac.models import TimingSession, Tag
from trac.serializers import TagSerializer
from trac.utils.user_util import is_athlete, is_coach
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import json


class TagViewSet(viewsets.ModelViewSet):
    """
    Returns a list of tags associated with the current user.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        """
        Overrides the default method to only return tags that belong to the
        user making the request.
        """
        user = self.request.user

        # If the user is an athlete, display the tags he owns.
        if is_athlete(user):
            tags = Tag.objects.filter(athlete_id=user.athlete.id)

        # If the user is a coach, list the tags owned by any of his athletes.
        elif is_coach(user):
            tags = Tag.objects.filter(
                       athlete__team__in=user.coach.team_set.all())
        
        # Otherwise, there are no tags to show.
        else:
            tags = Tag.objects.none()
        return tags


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def WorkoutTags(request):
    """
    Registered tags endpoint for settings.
    """
    if request.method == 'GET': #loadAthletes
        data = request.GET
        user = request.user

        id_num = int(data.get('id'))
        missed = data.get('missed', None) == 'true'
        
        array = []
        if not is_coach(user):
            return Response({}, status.HTTP_403_FORBIDDEN)
        else:
            table = TimingSession.objects.get(id=id_num)
            result = table.registered_tags.all()
            if missed:
                result = result.exclude(id__in=table.splits.values_list(
                                            'tag', flat=True).distinct())
            for instance in result:
                u_first = instance.athlete.user.first_name
                u_last = instance.athlete.user.last_name
                username = instance.athlete.user.username
                array.append({'id': instance.id, 'first': u_first,
                              'last': u_last, 'username': username,
                              'id_str': instance.id_str})
            
                return Response(array, status.HTTP_200_OK)
    
    elif request.method == 'POST':
        id_num = request.POST.get('id')
        tag_id = request.POST.get('id2')
        fname = request.POST.get('firstname')
        lname = request.POST.get('lastname')
        i_user = request.user
        if not is_coach(i_user):
            return Response({}, status.HTTP_403_FORBIDDEN)
        else:
            if request.POST.get('submethod') == 'Delete': #Delete
                ts = TimingSession.objects.get(id=id_num)
                tag = ts.registered_tags.get(id=tag_id)
                ts.registered_tags.remove(tag)
                return Response({}, status.HTTP_200_OK)
            
            elif request.POST.get('submethod') == 'Update': #Update and Create
                ts = TimingSession.objects.get(id=id_num)
                user, created = User.objects.get_or_create(
                                    username=request.POST.get('username'))
                a, created = Athlete.objects.get_or_create(user=user)
                if is_coach(i_user):
                    cp = Coach.objects.get(user=i_user)
                    #cp.athletes.add(a.pk)
                a.save()
                try:  #if tag exists update user. Or create tag.
                    user.first_name = fname
                    user.last_name = lname
                    tag = Tag.objects.get(id_str = request.POST.get('id_str'))
                    tag.athlete = a
                    tag.save()
                    user.save()
                except ObjectDoesNotExist:
                    try:
                        tag = Tag.objects.get(athlete = user.athlete)
                        tag.id_str = request.POST.get('id_str')
                        tag.save()
                    except ObjectDoesNotExist:
                        tag = Tag.objects.create(
                                id_str=request.POST.get('id_str'), user=user)
                
                ts.registered_tags.add(tag.pk)
                ts.save()
                return Response({}, status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def ManyDefaultTags(request):
    """
    Register tags to a session.
    """
    i_user = request.user
    if not is_coach(i_user):
        return Response({}, status.HTTP_403_FORBIDDEN)
    
    else:
        data = json.loads(request.body)
        for athlete in data['athletes']:
            atl = User.objects.get(username=athlete['username'])
            ts = TimingSession.objects.get(id=data['id'])
            try:
                tag = Tag.objects.get(athlete=atl.athlete)
            except:
                tag = Tag.objects.create(athlete=atl.athlete)
                tag.id_str = 'edit tag'
            tag.save()
            ts.registered_tags.add(tag.pk)
        ts.save()
        return Response({}, status.HTTP_200_OK)
