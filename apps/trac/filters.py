import django_filters

from trac.models import Athlete, Coach, TimingSession, Team, Split


class AthleteFilter(django_filters.FilterSet):
    session = django_filters.NumberFilter(name='split__timingsession',
                                          distinct=True)
    primary_team = django_filters.BooleanFilter(name='team__primary_team',
                                                distinct=True)
    team_name = django_filters.CharFilter(name='team__name')
    min_age = django_filters.MethodFilter()
    max_age = django_filters.MethodFilter()
    registered_to_session = django_filters.NumberFilter(
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


class CoachFilter(django_filters.FilterSet):
    team_name = django_filters.CharFilter(name='team__name')

    class Meta:
        model = Coach
        fields = (
            'team',
            'team_name'
        )


class TimingSessionFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        name='start_time', lookup_type='gte')
    stop_date = django_filters.DateFilter(
        name='start_time', lookup_type='lte')
    athlete = django_filters.NumberFilter(name='splits__athlete',
                                          distinct=True)

    class Meta:
        model = TimingSession
        fields = (
            'start_date',
            'stop_date',
            'private',
            'coach',
            'athlete'
        )


class TeamFilter(django_filters.FilterSet):

    class Meta:
        model = Team
        fields = (
            'name',
            'primary_team',
            'coach'
        )


class SplitFilter(django_filters.FilterSet):
    reader = django_filters.CharFilter(name='reader__id_str')
    tag = django_filters.CharFilter(name='tag__id_str')
    time_gte = django_filters.NumberFilter(name='time', lookup_type='gte')
    time_lte = django_filters.NumberFilter(name='time', lookup_type='lte')
    session = django_filters.NumberFilter(name='timingsession')

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
