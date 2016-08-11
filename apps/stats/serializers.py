from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from stats.models import PerformanceRecord
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

class PerformanceRecord_Serializer(serializers.ModelSerializer):

    class Meta:
        model = PerformanceRecord
        fields = ('athlete', 'event_name', 'distance', 'VO2', 'time', 'date')
