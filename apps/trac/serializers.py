from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from models import TimingSession, Tag, Reader, Athlete, Coach, Team
from trac.utils.util import is_coach, is_athlete


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


class AthleteSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    tag = serializers.RelatedField('tag.id_str')
    age = serializers.IntegerField(source='age', read_only=True)  

    class Meta:
        model = Athlete
        fields = ('id', 'username', 'tag','first_name','last_name',
                  'birth_date', 'gender', 'team', 'age') 
    
    def filter_team(self, queryset):
        """Only show teams belonging to the current coach."""
        if 'request' in self.context:
            user = self.context['request'].user
        
            if is_coach(user):
                teams = Team.objects.filter(coach=user.coach)
                return queryset.filter(pk__in=[team.pk for team in teams])

            else:
                return queryset.filter(pk=user.athlete.team.pk)

        return queryset
    

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        read_only_fields = ('coach',)


class CoachSerializer(serializers.ModelSerializer):

    class Meta:
        model = User


class TagSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='athlete.user.username',
                                     read_only=True)
    full_name = serializers.CharField(source='athlete.user.get_full_name',
                                      read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'id_str', 'username', 'full_name', 'athlete')

    def filter_athlete(self, queryset):
        """Only show athletes belonging to the current coach."""
        user = self.context['request'].user

        if is_coach(user):
            athletes = Athlete.objects.filter(team__in=user.coach.team_set.all())
            return queryset.filter(pk__in=[athlete.pk for athlete in athletes])
        
        else:
            return queryset.filter(pk=user.athlete.id)


class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)
    organization = serializers.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type', 'organization')


class ReaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reader
        fields = ('id', 'name', 'id_str')


class TimingSessionSerializer(serializers.ModelSerializer):
    coach = serializers.Field(source='coach.user.username')
    readers = serializers.RelatedField(many=True, read_only=True)

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        exclude = ('splits',)
        read_only_fields = ('registered_tags', )


class ScoringSerializer(serializers.ModelSerializer):

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name')


