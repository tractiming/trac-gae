import rest_framework_filters as filters

from stats.models import PerformanceRecord

class PerformanceRecord_Filter(filters.FilterSet):
    event_date = filters.DateFilter(name='date')
    event_name = filters.CharFilter(name='event_name')
    event_distance = filters.NumberFilter(name='distance')

    class Meta:
        model = PerformanceRecord
        fields = (
		'distance',
		'time',
		'interval',
		'VO2',
		'athlete',
		'coach',
		'date',
		'event_name',
        )
