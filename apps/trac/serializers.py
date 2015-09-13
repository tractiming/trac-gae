from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from models import TimingSession, Tag, Reader, Athlete, Coach, Team
from trac.utils.user_util import is_coach, is_athlete


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
        if 'request' in self.context:
            user = self.context['request'].user

            if is_coach(user):
                athletes = Athlete.objects.filter(team__in=user.coach.team_set.all())
                return queryset.filter(pk__in=[athlete.pk for athlete in athletes])
            else:
                return queryset.filter(pk=user.athlete.id)
        
        return queryset


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class AthleteSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    user = UserSerializer()
    tag = serializers.SlugRelatedField(read_only=True, slug_field='id_str')

    class Meta:
        model = Athlete
    
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

    def create(self, validated_data):
        user_info = validated_data.pop('user')
        user = User.objects.create(**user_info)
        athlete = Athlete.objects.create(user=user, **validated_data)
        return athlete
    

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        read_only_fields = ('coach',)


class CoachSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Coach
        fields = ('user', )


class RegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(max_length=15)
    organization = serializers.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type', 'organization')


class ReaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reader
        fields = ('id', 'name', 'id_str',)

    def create(self, validated_data):
        coach = Coach.objects.get(user=self.context['request'].user)
        reader = Reader.objects.create(coach=coach, **validated_data)
        return reader


class TimingSessionSerializer(serializers.ModelSerializer):
    coach = serializers.CharField(source='coach.user.username', read_only=True)
    readers = serializers.SlugRelatedField(many=True, read_only=True,
                                           slug_field='id_str')

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        exclude = ('splits',)
        read_only_fields = ('registered_tags', )

    def create(self, validated_data):
        coach = Coach.objects.get(user=self.context['request'].user)
        readers = Reader.objects.filter(coach=coach)
        session = TimingSession.objects.create(coach=coach, **validated_data)
        session.readers.add(*readers)
        return session


class ScoringSerializer(serializers.ModelSerializer):

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name')


