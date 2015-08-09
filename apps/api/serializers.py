from django.contrib.auth.models import User
from django.utils import timezone, simplejson as json
from rest_framework import serializers
from trac.models import TimingSession, Tag, Reader, Athlete, Coach, Team
from trac.util import is_coach, is_athlete

#class JSONReadOnlyField(serializers.Field):
#    """A custom serializer for rendering JSON."""
#
#    def to_native(self, obj):
#        return json.dumps(obj, encoding="utf8")
#
#    def from_native(self, value):
#        return json.loads(value)
'''
class FilterRelatedMixin(object):
    """Mixin to filter related objects."""
    def __init__(self, *args, **kwargs):
        super(FilterRelatedMixin, self).__init__(*args, **kwargs)

        for name, field in self.fields.iteritems():
            if isinstance(field, serializers.RelatedField):
                method_name = 'filter_%s' % name
                try:
                    func = getattr(self, method_name)
                except AttributeError:
                    pass
                else:
                    field.queryset = func(field.queryset)
'''

class UserSerializer(serializers.ModelSerializer):
    #tags = JSONReadOnlyField(source='athlete.get_tags')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'tags', 'email')


class AthleteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    team = serializers.CharField(source='team', required=False)
    
    class Meta:
        model = Athlete
        fields = ('id', 'username', 'age', 'gender', 'team') 


class TeamSerializer(serializers.ModelSerializer):
    athlete_set = AthleteSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        read_only_fields = ('coach',)


class CoachSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source='groups.all', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'organization')

#class TagSerializer(FilterRelatedMixin, serializers.ModelSerializer):
#    username = serializers.CharField(source='user.username', read_only=True)
#    first_name = serializers.CharField(source='user.first_name', read_only=True)
#    last_name = serializers.CharField(source='user.last_name', read_only=True)
#
#    class Meta:
#        model = Tag
#        fields = ('id', 'id_str', 'user', 'username','first_name','last_name')
#
#    def filter_user(self, queryset):
#        # Only show the users belonging to the current user,
#        user = self.context['request'].user
#
#        if is_coach(user):
#            pks = [a.user.pk for a in user.coach.athletes.all()]
#            return queryset.filter(pk__in=pks)
#        
#        else:
#            return queryset.filter(username=user.username)

class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)
    organization = serializers.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type', 'organization')


class ReaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reader


class TimingSessionSerializer(serializers.ModelSerializer):
    coach = serializers.Field(source='coach.user.username')
    readers = serializers.RelatedField(many=True, read_only=True)
    #start_time = serializers.DateTimeField()

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        exclude = ('splits',)
        read_only_fields = ('registered_tags', )
        #fields = ('id', 'name', 'start_time', 'stop_time',
        #          'start_button_time', 'private', 'filter_choice',
        #          'comment')

    '''
    def create(self, request):
        if request.DATA['start_time'] is None:
            request.DATA['start_time'] = str(timezone.now())
        if request.DATA['stop_time'] is None:
            request.DATA['stop_time'] = str(timezone.now())
        print request
        super(TimingSessionSerializer, self).create(request)
        #pass
    '''


class ScoringSerializer(serializers.ModelSerializer):
    #final_score = JSONReadOnlyField(source='individual_results')

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name')

#class CSVSerializer(serializers.Serializer):
#    csv_file = serializers.FileField(max_length=1000, allow_empty_file=False)
