from django.contrib.auth.models import User
from django.utils import timezone, simplejson as json
from rest_framework import serializers
from trac.models import TimingSession, Tag, Reader, AthleteProfile, CoachProfile
from trac.util import is_coach, is_athlete

class JSONReadOnlyField(serializers.Field):
    """A custom serializer for rendering JSON."""

    def to_native(self, obj):
        return json.dumps(obj, encoding="utf8")

    def from_native(self, value):
        return json.loads(value)

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

class UserSerializer(serializers.ModelSerializer):
    tags = JSONReadOnlyField(source='athlete.get_tags')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'tags', 'email')

class CoachSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source='groups.all', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'organization')

class TagSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'id_str', 'user', 'username','first_name','last_name')

    def filter_user(self, queryset):
        # Only show the users belonging to the current user,
        user = self.context['request'].user

        if is_coach(user):
            pks = [a.user.pk for a in user.coach.athletes.all()]
            return queryset.filter(pk__in=pks)
        
        else:
            return queryset.filter(username=user.username)

class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)
    organization = serializers.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type', 'organization')

class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ('id','name', 'id_str')

class TimingSessionSerializer(serializers.ModelSerializer):
    manager = serializers.Field(source='manager.username')
    #results = JSONReadOnlyField(source='get_results')
    #athletes = JSONReadOnlyField(source='get_athlete_names')
    #start_time = serializers.DateTimeField(allow_blank=True, required=False)

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name', 'start_time', 'stop_time')
        #fields = ('id', 'name', 'start_time', 'stop_time',
        #          'comment', 'rest_time', 'track_size', 'interval_distance', 
        #          'interval_number', 'filter_choice', 'manager',
        #          'results', 'athletes', 'start_button_time', 'private')
    
    #def get_validation_exclusions(self, instance=None):    
    #    exclusions = super(TimingSessionSerializer,
    #            self).get_validation_exclusions(instance)
    #    ex = exclusions + ['start_time']
    #    return ex

class ScoringSerializer(serializers.ModelSerializer):
    #final_results = JSONReadOnlyField(source='get_final_results')
    final_score = JSONReadOnlyField(source='get_ordered_results')
    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'final_score', 'name')
        
class CreateTimingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time', 'manager')
        

class CSVSerializer(serializers.Serializer):
    csv_file = serializers.FileField(max_length=1000, allow_empty_file=False)
