from django.contrib.auth.models import User
from django.utils import simplejson as json
from rest_framework import serializers

from trac.models import TimingSession, Tag, Reader, AthleteProfile

class JSONReadOnlyField(serializers.Field):
    """A custom serializer for rendering JSON."""

    def to_native(self, obj):
        return json.dumps(obj, encoding="utf8")

    def from_native(self, value):
        return json.loads(value)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')

class AthleteProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.Field(source='user.username')
    tags = JSONReadOnlyField(source='get_tags')

    class Meta:
        model = AthleteProfile
        fields = ('full_name', 'tags')

class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id_str',)
        
class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ('name', 'id_str')

class TimingSessionSerializer(serializers.ModelSerializer):
    manager = serializers.Field(source='manager.username')
    results = JSONReadOnlyField(source='get_results')
    athletes = JSONReadOnlyField(source='get_athletes')

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name', 'start_time', 'stop_time', 'manager',
                'results', 'athletes')

class CreateTimingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time', 'manager')
        
