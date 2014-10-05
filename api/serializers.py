from django.contrib.auth.models import User
from rest_framework import serializers

from common.models import TimingSession

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')

        
class TimingSessionSerializer(serializers.HyperlinkedModelSerializer):
    manager = serializers.Field(source='manager.username')
    results = serializers.HyperlinkedIdentityField(view_name='timingsession-results',
                                                   format='json')

    class Meta:
        model = TimingSession
        fields = ('url', 'name', 'start_time', 'stop_time', 'manager', 'results')
