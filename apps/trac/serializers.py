from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from models import TimingSession, Tag, Reader, Athlete, Coach, Team, Split
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
        user = User.objects.create(last_login=timezone.now(), **user_info)
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


class SplitSerializer(serializers.ModelSerializer):
    reader = serializers.SlugRelatedField(slug_field='id_str',
                                          allow_null=True,
                                          queryset=Reader.objects.all())
    tag = serializers.SlugRelatedField(slug_field='id_str',
                                       allow_null=True, required=False,
                                       queryset=Tag.objects.all())
    sessions = serializers.PrimaryKeyRelatedField(many=True, 
        queryset=TimingSession.objects.all(), allow_null=True,
        source='timingsession_set')
    athlete = serializers.PrimaryKeyRelatedField(many=False,
        queryset=Athlete.objects.all(), allow_null=True)

    def __init__(self, *args, **kwargs):
        try:
            user = kwargs['context']['request'].user
        except KeyError: # swagger
            return super(SplitSerializer, self).__init__(*args, **kwargs)

        sessions_f = self.fields['sessions']
        sessions_f.child_relation.queryset = (
                sessions_f.child_relation.queryset.filter(coach__user=user))

        readers_f = self.fields['reader']
        readers_f.queryset = readers_f.queryset.filter(coach__user=user)

        return super(SplitSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Split
        lookup_field = 'split'

    def validate(self, data):
        # Must specify either an athlete or a tag.
        if not any((data['athlete'], data['tag'])):
            raise serializers.ValidationError('Must specify at least one of '
                                              '"user", "tag".')
        # Must specify either a reader or a session.
        if not any((data['reader'], data['timingsession_set'])):
            raise serializers.ValidationError('Must specify at least one of '
                                              '"reader", "session".')
        return super(SplitSerializer, self).validate(data)

    def create(self, validated_data):
        """
        NOTE: expecting request to either specify session/athlete OR
        reader/tag when creating a split.
        """
        # If athlete not specified, get the athlete currently assigned to the
        # tag. The validator ensures either the tag or the athlete is given.
        if validated_data['athlete'] is None:
            validated_data['athlete'] = validated_data['tag'].athlete

        split = super(SplitSerializer, self).create(validated_data)
        
        # If the session(s) is not given explicitly, add splits to sessions
        # based on the reader's active sessions.
        if not split.timingsession_set.exists() and split.reader is not None:
            for session in split.reader.active_sessions:
                # If the session has a set of registered tags, and the current
                # tag is not in that set, ignore the split.
                if (session.use_registered_tags_only and
                        (split.tag is None or
                            split.tag not in session.registered_tags.all())):
                    continue
                session.splits.add(split.pk)

                # Destroying the cache for this session will force the results
                # to be recalculated. Athlete is a required field on split, so
                # the id will always exist.
                session.clear_cache(split.athlete.id)

        return split
