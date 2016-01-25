from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from trac.models import (
    TimingSession, Tag, Reader, Athlete, Coach, Team, Split
)
from trac.utils.user_util import is_coach, is_athlete, user_type


class FilterRelatedMixin(object):
    """Mixin to filter related objects."""
    def __init__(self, *args, **kwargs):
        super(FilterRelatedMixin, self).__init__(*args, **kwargs)

        for name, field in self.fields.iteritems():
            if isinstance(field, (serializers.RelatedField,
                                  serializers.ManyRelatedField)):
                method_name = 'filter_%s' % name
                try:
                    func = getattr(self, method_name)
                except AttributeError:
                    pass
                else:
                    if hasattr(field, 'child_relation'):
                        field.child_relation.queryset = func(
                            field.child_relation.queryset)
                    else:
                        field.queryset = func(field.queryset)


class TagSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='athlete.user.username',
                                     read_only=True)
    full_name = serializers.CharField(source='athlete.user.get_full_name',
                                      read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'id_str', 'username', 'full_name', 'athlete', 'bib')

    def filter_athlete(self, queryset):
        """Only show athletes belonging to the current coach."""
        if 'request' in self.context:
            user = self.context['request'].user

            if is_coach(user):
                athletes = Athlete.objects.filter(
                    team__in=user.coach.team_set.all())
                queryset = queryset.filter(
                    pk__in=[athlete.pk for athlete in athletes])
            elif is_athlete(user):
                queryset = queryset.filter(pk=user.athlete.id)
            else:
                queryset = queryset.none()

        return queryset


class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password',
            'user_type', 'last_login'
        )
        read_only_fields = ('last_login',)
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def get_user_type(self, obj):
        return user_type(obj)

    def create(self, validated_data):
        # Override to ensure we call `set_password`.
        password = validated_data.pop('password', None)
        user = User.objects.create(last_login=timezone.now(),
                                   **validated_data)
        user.set_password(password)
        user.save()
        return user


class SaveUserMixin(object):
    """Convenience mixin that provides `create` and `update` methods
    for model serializers with a nested `user` attribute, e.g.
    `AthleteSerializer` and `CoachSerializer`.
    """
    def create(self, validated_data):
        """Extract user data, create the user, and use to create the
        higher-level object.
        """
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.create(user_serializer.validated_data)
        validated_data.update({'user_id': user.id})

        return super(SaveUserMixin, self).create(validated_data)

    def update(self, instance, validated_data):
        """Update all of the user fields making sure to call
        `set_password`.
        """
        user_data = validated_data.pop('user', None)
        if user_data is not None:
            for attr, value in user_data.items():
                if attr == 'password':
                    instance.user.set_password(value)
                else:
                    setattr(instance.user, attr, value)

            # If username is not unique, the save will fail.
            try:
                instance.user.save()
            except Exception:
                raise ValidationError('Invalid username')

        return super(SaveUserMixin, self).update(instance, validated_data)


class AthleteSerializer(SaveUserMixin,
                        FilterRelatedMixin,
                        serializers.ModelSerializer):
    tag = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='id_str', allow_null=True,
        required=False)
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name',
                                       required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    password = serializers.SlugField(source='user.password', write_only=True,
                                     required=False)
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), allow_null=True, required=False)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = Athlete
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'team', 'age', 'birth_date', 'gender', 'tfrrs_id', 'tag',
            'password', 'team_name'
        )
        read_only_fields = ('age',)

    def filter_team(self, queryset):
        # Only allow teams owned by the current user. Note that this
        # is for validation only.
        if 'request' in self.context:
            user = self.context['request'].user

            if is_coach(user):
                queryset = queryset.filter(coach__user=user)
            elif is_athlete(user):
                queryset = queryset.filter(athlete__user=user)
            else:
                queryset = queryset.none()

        return queryset


class CoachSerializer(SaveUserMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name',
                                       required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    password = serializers.SlugField(source='user.password', write_only=True,
                                     required=False)
    teams = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='timingsession_set')

    class Meta:
        model = Coach
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'password', 'teams'
        )
        read_only_fields = ('teams',)


class TeamSerializer(serializers.ModelSerializer):
    coach = serializers.IntegerField(read_only=True, source='coach.id')

    class Meta:
        model = Team

    def create(self, validated_data):
        """Set the team's coach to match the current user."""
        coach = get_object_or_404(Coach, user=self.context['request'].user)
        return Team.objects.create(coach=coach, **validated_data)


class ReaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reader
        fields = ('id', 'name', 'id_str',)

    def create(self, validated_data):
        coach = Coach.objects.get(user=self.context['request'].user)
        reader = Reader.objects.create(coach=coach, **validated_data)
        return reader


class TimingSessionSerializer(FilterRelatedMixin,
                              serializers.ModelSerializer):
    coach = serializers.CharField(source='coach.user.username', read_only=True)
    readers = serializers.SlugRelatedField(many=True, read_only=True,
                                           slug_field='id_str')
    registered_athletes = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Athlete.objects.all(), allow_null=True,
        required=False)

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        exclude = ('splits',)

    def filter_registered_athletes(self, queryset):
        """Only show athletes belonging to the current coach."""
        if 'request' in self.context:
            user = self.context['request'].user

            if is_coach(user):
                queryset = queryset.filter(
                    team__in=user.coach.team_set.all(),
                    team__isnull=False)
            elif is_athlete(user):
                queryset = queryset.filter(user=user)
            else:
                queryset = queryset.none()

        return queryset

    def create(self, validated_data):
        # TODO: ensure the user is a coach
        coach = Coach.objects.get(user=self.context['request'].user)
        readers = Reader.objects.filter(coach=coach)
        validated_data['coach'] = coach
        session = super(TimingSessionSerializer, self).create(validated_data)
        session.readers.add(*readers)
        return session


class ScoringSerializer(serializers.ModelSerializer):

    class Meta:
        model = TimingSession
        lookup_field = 'session'
        fields = ('id', 'name')


class SplitSerializer(FilterRelatedMixin, serializers.ModelSerializer):
    reader = serializers.SlugRelatedField(slug_field='id_str',
                                          allow_null=True,
                                          queryset=Reader.objects.all())
    tag = serializers.SlugRelatedField(slug_field='id_str',
                                       allow_null=True, required=False,
                                       queryset=Tag.objects.all())
    sessions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TimingSession.objects.all(), allow_null=True,
        source='timingsession_set')
    athlete = serializers.PrimaryKeyRelatedField(
        many=False, queryset=Athlete.objects.all(), allow_null=True)

    class Meta:
        model = Split
        lookup_field = 'split'

    def filter_sessions(self, queryset):
        if 'request' in self.context:
            user = self.context['request'].user
            if not user.is_superuser:
                queryset = queryset.filter(coach__user=user)
        return queryset

    def filter_reader(self, queryset):
        if 'request' in self.context:
            user = self.context['request'].user
            if not user.is_superuser:
                queryset = queryset.filter(coach__user=user)
        return queryset

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
            sessions = split.reader.active_sessions
            for session in sessions:
                # If the session has a set of registered athletes, and the
                # current tag is not in that set, ignore the split.
                if (session.use_registered_athletes_only and
                        split.athlete not in
                        session.registered_athletes.all()):
                    continue
                session.splits.add(split.pk)
        else:
            sessions = split.timingsession_set.all()

        for session in sessions:
            # Destroying the cache for this session will force the results
            # to be recalculated. Athlete is a required field on split, so
            # the id will always exist.
            session.clear_cache(split.athlete.id)

        return split
