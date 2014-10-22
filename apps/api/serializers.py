from django.contrib.auth.models import User
from rest_framework import serializers

from trac.models import TimingSession, Tag, Reader, AthleteProfile

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')

class AthleteProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AthleteProfile

class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id_str')
        
class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ('name', 'id_str')

class TimingSessionSerializer(serializers.HyperlinkedModelSerializer):
    manager = serializers.Field(source='manager.username')
    results =\
    serializers.HyperlinkedIdentityField(view_name='TimingSession-results',
            format='json')

    class Meta:
        model = TimingSession
        fields = ('url', 'name', 'start_time', 'stop_time', 'manager', 'results')

class CreateTimingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time', 'manager')
        
