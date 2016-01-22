import rest_framework_filters as filters

from trac.models import Athlete, Coach, TimingSession, Team, Split


class AthleteFilter(filters.FilterSet):
    session = filters.NumberFilter(name='split__timingsession',
                                   distinct=True)
    primary_team = filters.BooleanFilter(name='team__primary_team',
                                         distinct=True)
    team_name = filters.CharFilter(name='team__name')
    min_age = filters.MethodFilter()
    max_age = filters.MethodFilter()
    registered_to_session = filters.NumberFilter(
        name='timingsession', distinct=True)

    class Meta:
        model = Athlete
        fields = (
            'session',
            'gender',
            'tfrrs_id',
            'primary_team',
            'team',
            'team_name',
            'min_age',
            'max_age',
            'registered_to_session'
        )

    def filter_min_age(self, queryset, value):
        """Minimum age."""
        try:
            age = int(value)
        except ValueError:
            return queryset.none()
        athlete_ids = (
            [athlete.id for athlete in queryset if athlete.age() >= age]
        )
        return queryset.filter(pk__in=athlete_ids)

    def filter_max_age(self, queryset, value):
        """Maximum age."""
        try:
            age = int(value)
        except ValueError:
            return queryset.none()
        athlete_ids = (
            [athlete.id for athlete in queryset if athlete.age() <= age]
        )
        return queryset.filter(pk__in=athlete_ids)


class CoachFilter(filters.FilterSet):
    team_name = filters.CharFilter(name='team__name')

    class Meta:
        model = Coach
        fields = (
            'team',
            'team_name'
        )


class TimingSessionFilter(filters.FilterSet):
    start_date = filters.DateFilter(name='start_time', lookup_type='gte')
    stop_date = filters.DateFilter(name='start_time', lookup_type='lte')
    athlete = filters.NumberFilter(name='splits__athlete', distinct=True)

    class Meta:
        model = TimingSession
        fields = (
            'start_date',
            'stop_date',
            'private',
            'coach',
            'athlete'
        )


class TeamFilter(filters.FilterSet):

    class Meta:
        model = Team
        fields = (
            'name',
            'primary_team',
            'coach'
        )


class SplitFilter(filters.FilterSet):
    reader = filters.CharFilter(name='reader__id_str')
    tag = filters.CharFilter(name='tag__id_str')
    time_gte = filters.NumberFilter(name='time', lookup_type='gte')
    time_lte = filters.NumberFilter(name='time', lookup_type='lte')
    session = filters.NumberFilter(name='timingsession')

    class Meta:
        model = Split
        fields = (
            'athlete',
            'tag',
            'session',
            'reader',
            'time_lte',
            'time_gte'
        )
