from django.contrib.auth.models import User
from django.utils import simplejson as json
from rest_framework import serializers

from trac.models import (TimingSession, Tag, Reader, AthleteProfile,
                         CoachProfile)
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
        fields = ('first_name', 'last_name', 'username', 'tags', 'id')

class TagSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'id_str', 'user', 'username')

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

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type')

class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ('id','name', 'id_str')

class TimingSessionSerializer(serializers.ModelSerializer):
    manager = serializers.Field(source='manager.username')
    results = JSONReadOnlyField(source='get_results')
    athletes = JSONReadOnlyField(source='get_athlete_names')

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name', 'start_time', 'stop_time','comment','rest_time','track_size','interval_distance','interval_number', 'filter_choice', 'manager',
                'results', 'athletes')

class CreateTimingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time', 'manager')
        
