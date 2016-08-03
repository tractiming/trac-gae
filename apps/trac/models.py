import datetime
from collections import namedtuple
from collections import Counter

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_delete, post_delete, m2m_changed
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils import timezone

from trac.utils.split_util import convert_units, format_total_seconds


def _upload_to(instance, filename):
    return '/'.join(('team-logo', str(instance.id), filename))


class Coach(models.Model):
    """
    A coach is a type of user who has a team of athletes, creates workouts,
    and owns readers.
    """
    user = models.OneToOneField(User)
    payment = models.CharField(max_length=25, null=True, blank=True)

    def __unicode__(self):
        return "name={}".format(self.user.username)

    class Meta:
        verbose_name_plural = 'coaches'


class Team(models.Model):
    """
    A team has one coach and many athletes.
    """
    name = models.CharField(max_length=50)
    coach = models.ForeignKey(Coach)
    tfrrs_code = models.CharField(max_length=20, unique=True, null=True,
                                  blank=True)
    primary_team = models.BooleanField(default=False)
    public_team = models.BooleanField(default=False)
    logo = models.ImageField(upload_to=_upload_to, blank=True, null=True)

    class Meta:
        unique_together = ("name", "coach",)

    def __unicode__(self):
        return "team_name={}".format(self.name)


class Athlete(models.Model):
    """
    An athlete is a type of user that owns tags and appears in workout
    results.
    """
    user = models.OneToOneField(User)
    team = models.ForeignKey(Team, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True)
    tfrrs_id = models.CharField(max_length=20, null=True, blank=True)
    year = models.CharField(max_length=10, null=True, blank=True)

    def __unicode__(self):
        return "name={}".format(self.user.username)

    def age(self, as_of_date=None):
        """Athlete's current age (in years)."""
        if not self.birth_date:
            return None

        if as_of_date is None:
            today = datetime.date.today()
        else:
            today = as_of_date

        try:
            birthday = self.birth_date.replace(year=today.year)
        except ValueError:
            birthday = self.birth_date.replace(year=today.year,
                                               month=born.month+1,
                                               day=1)
        if birthday > today:
            return today.year-self.birth_date.year-1
        else:
            return today.year-self.birth_date.year


class Tag(models.Model):
    """
    An RFID tag that is worn by an athlete. Each athlete can have only one tag.
    """
    id_str = models.CharField(max_length=50, unique=True)
    bib = models.CharField(max_length=25, null=True, blank=True)
    athlete = models.OneToOneField(Athlete)

    def __unicode__(self):
        return "id={}, athlete={}".format(self.id_str, self.athlete.user.username)


class Reader(models.Model):
    """
    An RFID reader that streams splits.
    """
    name = models.CharField(max_length=50)
    id_str = models.CharField(max_length=50, unique=True)
    coach = models.ForeignKey(Coach)

    class Meta:
        unique_together = ('coach', 'name',)

    def __unicode__(self):
        return "id={}, name={}".format(self.id_str, self.name)

    @property
    def active_sessions(self):
        """
        Returns a list of all active sessions the reader belongs to.
        """
        now = timezone.now()
        return self.timingsession_set.filter(start_time__lte=now,
                                             stop_time__gte=now)


class Split(models.Model):
    """
    A single split time from one tag.
    """
    tag = models.ForeignKey(Tag, null=True, blank=True, on_delete=models.SET_NULL)
    athlete = models.ForeignKey(Athlete)
    reader = models.ForeignKey(Reader, null=True, blank=True, on_delete=models.SET_NULL)
    time = models.BigIntegerField()

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        tag = '' if self.tag is None else self.tag.id_str
        reader = '' if self.reader is None else self.reader.id_str
        return "time={}, tag={}, reader={}".format(
                self.time, tag, reader)

    def distance(self, session, units='miles'):
        """Get the distance in the race at which this split was taken.
        Returns None if this split was not taken at a known checkpoint.
        """
        assert self in session.splits.all(), 'Split not in given session'

        checkpoint = session.checkpoint_set.filter(
            readers=self.reader).first()
        if not checkpoint or checkpoint.distance is None:
            return None

        _units = {'mi': 'miles', 'm': 'meters', 'km': 'kilometers'}
        return convert_units(checkpoint.distance,
                             _units[checkpoint.distance_units],
                             units)

    def calc_pace(self, session, distance_units='miles'):
        """Calculate pace per mile for this split (if applicable)."""
        current_time = self.time
        current_distance = self.distance(session, units=distance_units)

        previous_split = session.splits.filter(
            time__lt=self.time,
            athlete=self.athlete,
            splitfilter__filtered=False).order_by('-time').first()

        if previous_split is None:
            if session.start_button_time is None:
                # This split is the first in the session, can't calculate
                # pace.
                return None
            else:
                previous_time = session.start_button_time
                previous_distance = 0.0
        else:
            previous_time = previous_split.time
            previous_distance = previous_split.distance(session,
                                                        units=distance_units)

        if current_distance is None or previous_distance is None:
            return None

        pace_seconds = (((current_time - previous_time) /
                        (current_distance - previous_distance)) / 1000.0)
        return '{} min/{}'.format(format_total_seconds(pace_seconds),
                                  distance_units[:-1])


class TimingSession(models.Model):
    """
    A collection of timing information, e.g. a workout or race.
    """
    name = models.CharField(max_length=50)
    coach = models.ForeignKey(Coach)
    readers = models.ManyToManyField(Reader)
    splits = models.ManyToManyField(Split, through='SplitFilter')

    start_time = models.DateTimeField(default=timezone.now, blank=True)
    stop_time = models.DateTimeField(default=timezone.now, blank=True)
    start_button_time = models.BigIntegerField(null=True, blank=True)
    registered_athletes = models.ManyToManyField(Athlete)
    use_registered_athletes_only = models.BooleanField(default=False)
    private = models.BooleanField(default=True)

    comment = models.CharField(max_length=2500, blank=True)
    rest_time = models.IntegerField(default=0, blank=True)
    track_size = models.IntegerField(default=400, blank=True)
    interval_distance = models.IntegerField(default=200, blank=True)
    interval_number = models.IntegerField(default=0, blank=True)

    filter_choice = models.BooleanField(default=True)
    filter_time = models.IntegerField(default=10, blank=True)
    filter_max_num_splits = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "num={}, name={}, coach={}".format(
            self.id, self.name, self.coach.user.username)

    @property
    def num_athletes(self):
        """Number of unique athletes seen in this workout."""
        return self.splits.values('athlete_id').distinct().count()

    @property
    def active(self):
        """
        Returns True if the current time is between the start and stop times.
        """
        now = timezone.now()
        return ((now > self.start_time) and (now < self.stop_time))

    def refresh_split_filters(self):
        """For each split in this session, recalculate whether the split
        should be filtered out of the results.
        """
        for splitfilter in self.splitfilter_set.all():
            splitfilter.filtered = splitfilter.determine_filter()
            splitfilter.save()

    def _sorted_athlete_list(self, limit=None, offset=None, gender=None,
                             age_lte=None, age_gte=None, teams=None,
                             apply_filter=True, exclude_nt=False):
        """Return IDs of all distinct athletes seen in this workout.

        The athlete IDs are ordered according to cumulative time. Therefore,
        results calculated by iterating over the list of returned IDs will
        already be in order.

        An optional list of filters can be applied to the athletes in the
        results set.
        """
        athlete_filter = models.Q()
        race_date = self.start_time.date()
        if gender is not None:
            assert gender.upper() in ['M', 'F'], "Invalid gender."
            athlete_filter &= models.Q(athlete__gender=gender.upper())
        if age_lte is not None:
            athlete_ids = [
                split.athlete.id for split in self.splits.all()
                if split.athlete.age(as_of_date=race_date) >= age_gte
            ]
            athlete_filter &= models.Q(athlete_id__in=athlete_ids)
        if age_gte is not None:
            athlete_ids = [
                split.athlete.id for split in self.splits.all()
                if split.athlete.age(as_of_date=race_date) <= age_lte
            ]
            athlete_filter &= models.Q(athlete_id__in=athlete_ids)
        if teams:
            athlete_filter &= models.Q(athlete__team__name__in=teams)

        if self.start_button_time is None:
            min_time = models.Min('time')
            min_split_count = 2
        else:
            min_time = self.start_button_time
            min_split_count = 1

        notime_filter = (models.Q(num_splits__gte=min_split_count)
                         if exclude_nt else models.Q())

        filter_ = (models.Q(splitfilter__filtered=False) if apply_filter
                   else models.Q())

        results = (self.splits.filter(athlete_filter & filter_)
                              .values('athlete_id')
                              .annotate(diff=models.Max('time')-min_time,
                                        num_splits=models.Count('splitfilter'))
                              .filter(notime_filter)
                              .order_by('diff')[offset:limit])

        return (athlete['athlete_id'] for athlete in results)

    def _calc_athlete_splits(self, athlete_id, use_cache=True,
                             apply_filter=True, calc_paces=False):
        """Calculate splits for a single athlete.

        First try to read results from the cache. If results are not found,
        get the tag and all its times. Iterate through times to calculate
        splits. Save new results to cache.

        Returns namedtuple of (user id, name, team, splits, total,
        first_seen, paces)
        """
        # Try to read from the cache. Note that results are cached on a per
        # tag basis.
        if use_cache:
            results = cache.get(('ts_%i_athlete_%i_results'
                                 %(self.id, athlete_id)))
        else:
            results = None

        Results = namedtuple(
            'Results',
            'user_id name team splits total first_seen last_seen paces bib gender age')
        if not results:
            athlete = Athlete.objects.get(id=athlete_id)
            name = athlete.user.get_full_name() or athlete.user.username

            filter_ = (models.Q(splitfilter__filtered=False) if apply_filter
                       else models.Q())
            raw_splits = self.splits.filter(
                filter_, athlete_id=athlete.id).order_by('time')
            times = list(raw_splits.values_list('time', flat=True))

            # Offset for start time if needed.
            if self.start_button_time is not None:
                times.insert(0, self.start_button_time)

            splits = [
                round((t2 - t1)/1000.0, 3) for t1, t2 in zip(times, times[1:])
            ]

            if len(times) > 0:
                raw_time = timezone.datetime.utcfromtimestamp(times[0]/1000.0)
                first_seen = raw_time.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

                last_split = timezone.datetime.utcfromtimestamp(times[-1]/1000.0)
                last_seen = last_split.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

            else:
                first_seen = None
                last_seen = None

            if calc_paces:
                distances = [split.distance(self) for split in raw_splits]
                if self.start_button_time is not None:
                    distances.insert(0, 0.0)

                paces = []
                for i, diff in enumerate(zip(distances, distances[1:])):
                    if diff[0] is not None and diff[1] is not None:
                        pace = '{} min/mile'.format(format_total_seconds(
                            splits[i] / (diff[1] - diff[0])))
                    else:
                        pace = None
                    paces.append(pace)

            else:
                paces = None

            try:
                bib = athlete.tag.bib
            except ObjectDoesNotExist:
                bib = None

            try:
                gender = athlete.gender
            except ObjectDoesNotExist:
                gender = None

            try:
                age = athlete.age()
            except ObjectDoesNotExist:
                age = None

            results = (athlete_id, name, athlete.team, splits,
                       sum(splits), first_seen, last_seen, paces, bib, gender, age)

            if use_cache:
                cache.set(('ts_%i_athlete_%i_results'
                          %(self.id, athlete_id)), results)

        return Results(*results)

    def individual_results(self, limit=None, offset=None, gender=None,
                           age_lte=None, age_gte=None, teams=None,
                           apply_filter=None, athlete_ids=None,
                           calc_paces=False, exclude_nt=False):
        """Calculate individual results for a session.

        First call `_sorted_athlete_list` for a list of tag IDs that are
        presorted by total time. Splice based on limit/offset and calc
        results one ID at a time.

        If `athlete_ids` is given explicitly, calculate results for those
        athletes only. This option overrides any other filters or
        limit/offset.

        Individual results can also be filtered by age, gender, etc.
        """
        if apply_filter is None:
            apply_filter = self.filter_choice

        if athlete_ids is not None:
            athletes = list(set(athlete_ids))
        else:
            athletes = self._sorted_athlete_list(limit=limit,
                                                 offset=offset,
                                                 gender=gender,
                                                 age_lte=age_lte,
                                                 age_gte=age_gte,
                                                 teams=teams,
                                                 apply_filter=apply_filter,
                                                 exclude_nt=exclude_nt)

        return [self._calc_athlete_splits(athlete,
                                          apply_filter=apply_filter,
                                          calc_paces=calc_paces)
                for athlete in athletes]

    def team_results(self, num_scorers=5):
        """Calculate team scores.

        Compute the individual scores and compile a list of team names.
        Iterate through the runners and add their place to each team's score.
        """
        individual_results = self.individual_results()
        #team_names = set([runner.team for runner in individual_results
        #                   if runner.team is not None])

        team_names = Counter([runner.team for runner in individual_results
                            if runner.team is not None])
        print team_names

        scores = {}
        for team in team_names:
            print team_names[team]
            scores[team] = {
                'athletes': [],
                'score': 0,
                'id': team.id,
                'name': team.name,
                'num_athletes' : team_names[team],
                'num_scorers' : num_scorers
            }

        place = 1
        team_place = 1
        for athlete in individual_results:
            # Runners not on a team do not score or affect other scores.
            if athlete.team in scores and scores[athlete.team]['num_athletes'] >= num_scorers:
                if len(scores[athlete.team]['athletes']) < num_scorers:
                    scores[athlete.team]['athletes'].append({
                        'name': athlete.name,
                        'ind_place': place,
                        'place' : team_place, #This is the team scored place.
                        'total': athlete.total
                    })
                    scores[athlete.team]['score'] += team_place
                elif len(scores[athlete.team]['athletes']) < num_scorers+2:
                    scores[athlete.team]['athletes'].append({
                        'name' : athlete.name,
                        'ind_place' : place,
                        'place' : team_place,
                        'total' : athlete.total
                    })
                else:
                    continue
                team_place += 1
                place += 1
            elif athlete.team in scores:
                scores[athlete.team]['athletes'].append({
                    'name' : athlete.name,
                    'ind_place' : place,
                    'place' : 0,
                    'total' : athlete.total
                })
                place += 1

        teams_with_enough_runners = (
                [scores[team] for team in scores if
                 len(scores[team]['athletes']) > 0])

        return sorted(teams_with_enough_runners, key=lambda x: x['score'])

    def clear_results(self):
        """Remove all the splits that currently exist in the session."""
        athlete_ids = self.splits.values_list('athlete_id',
                                              flat=True).distinct()
        for athlete_id in athlete_ids:
            self.clear_cache(athlete_id)

        # Clear the link between split and session. Only delete the split if
        # it does not belong to any other sessions.
        self.splits.clear()
        Split.objects.filter(timingsession=None).delete()

    def clear_cache(self, athlete_id):
        """Clear the session's cached results for a single tag."""
        cache.delete(('ts_%i_athlete_%i_results' %(self.id, athlete_id)))

    def clear_cache_all(self):
        """Clear the cache for all participating athletes. Include athletes
        that are registered, as well as those who show up in the results.
        """
        athlete_ids = (
            set(self.splits.values_list('athlete_id', flat=True)) |
            set(self.registered_athletes.values_list('id', flat=True))
        )
        for athlete_id in athlete_ids:
            self.clear_cache(athlete_id)



    # TODO: Move to utils.
    def _delete_split(self, athlete_id, split_indx):
        """
        Delete a result from the array of splits. The split index should refer
        to the position of the split in the unfiltered results.
        """
        assert self.filter_choice is False, "Filter must be off to delete."
        splits = self.splits.filter(athlete_id=athlete_id).order_by('time')
        athlete = Athlete.objects.get(id=athlete_id)

        if self.start_button_time is not None:
            indx = split_indx
        else:
            indx = split_indx + 1

        results = self._calc_athlete_splits(athlete.id, apply_filter=False)
        offset_ms = int(results.splits[split_indx] * 1000)
        splits[indx].delete()

        # Edit the rest of the splits to maintain the other splits.
        for i in range(indx, len(splits)):
            splits[i].time = splits[i].time - offset_ms
            splits[i].save()

    # TODO: Move to utils.
    def _insert_split(self, athlete_id, split_indx, val, shift):
        """
        Insert a new split into the array before the given index.
        Can specify whether to shift following splits.
        """
        assert self.filter_choice is False, "Filter must be off to insert."

        tt = self.splits.filter(athlete_id=athlete_id).order_by('time')
        split_dt = val

        # Find the index of the first tag time we need to change as well as
        # the previous (absolute) time.
        if self.start_button_time is not None:
            indx = split_indx
            if indx == 0:
                t_prev = self.start_button_time
            else:
                t_prev = tt[indx-1].time
        else:
            indx = split_indx + 1
            t_prev = tt[indx-1].time

        t_curr = t_prev + split_dt
        nt = Split.objects.create(athlete_id=athlete_id, time=t_curr)

        # Edit the rest of the tagtimes to maintain the other splits.
        if shift:
            for i in list(reversed(range(indx, len(tt)))):
                cur_tt = tt[i]
                cur_tt.time = cur_tt.time+split_dt
                cur_tt.save()

        self.splitfilter_set.create(split=nt)

    # TODO: Move to utils.
    def _edit_split(self, athlete_id, split_indx, val):
        """
        Change the value of a split in the list of results. The split index
        should refer to the position in the unfiltered results.

        The split is edited by deleting the current time and inserting a new
        split in its place.
        """
        assert self.filter_choice is False, "Filter must be off to edit."
        self._delete_split(athlete_id, split_indx)
        self._insert_split(athlete_id, split_indx, val, True)

    # TODO: Move to utils.
    def _overwrite_final_time(self, athlete_id, hr, mn, sc, ms):
        """
        Force a final time for a given athlete. This will delete all
        existing splits and assign a final time only.
        """
        self.splits.filter(athlete_id=athlete_id).delete()

        if self.start_button_time is None:
            split = Split.objects.create(athlete_id=athlete_id, time=0)
            self.splitfilter_set.create(split=split)
            start_time = split.time
        else:
            start_time = self.start_button_time

        final_time = start_time + (3600000*hr + 60000*mn + 1000*sc + ms)
        split = Split.objects.create(athlete_id=athlete_id, time=final_time)
        self.splitfilter_set.create(split=split)

    def _unlink_splits(self, athlete_id):
        """
        Unlink splits that belong to one timing session, but dont belong in another
        without deleting them. It removes the link between the split and the 
        SplitFilter model
        """

        ath_splits = self.splits.filter(athlete_id=athlete_id)

        for split in ath_splits:
            try:
                split.splitfilter_set.filter(timingsession__id=self.id).first().delete()
            except (ValueError, ObjectDoesNotExist):
                pass


class SplitFilter(models.Model):
    """
    Extra information about whether a split should be filtered from the
    results in a given session.
    """
    timingsession = models.ForeignKey(TimingSession)
    split = models.ForeignKey(Split)
    filtered = models.BooleanField(default=False)

    class Meta:
        db_table = 'trac_timingsession_splits'
        unique_together = ('timingsession', 'split')

    def determine_filter(self, min_time=None):
        """Determine if a split should be filtered from the results."""
        previous_splits = self.timingsession.splits.filter(
            athlete=self.split.athlete,
            time__lt=self.split.time)
        most_recent_time = (previous_splits.aggregate(models.Max('time')).get(
            'time__max') or self.timingsession.start_button_time)

        if most_recent_time is not None:
            min_seconds = min_time or 1000*self.timingsession.filter_time
            time_filter = (self.split.time - most_recent_time) < min_seconds
        else:
            time_filter = False

        max_num = self.timingsession.filter_max_num_splits
        if max_num is not None:
            num_filter = previous_splits.filter(
                splitfilter__filtered=False,
                timingsession=self.timingsession).count() >= max_num
        else:
            num_filter = False

        return (time_filter or num_filter)

    def save(self, *args, **kwargs):
        if not self.pk:
            # If being created, determine if the split should be
            # filtered in the results.
            self.filtered = self.determine_filter()
        return super(SplitFilter, self).save(*args, **kwargs)


class Checkpoint(models.Model):
    """
    A checkpoint encodes where each reader is located in a race.
    """
    name = models.CharField(max_length=50)
    session = models.ForeignKey(TimingSession)
    readers = models.ManyToManyField(Reader)
    distance = models.FloatField(null=True, blank=True)

    METERS = 'm'
    KILOMETERS = 'km'
    MILES = 'mi'
    DISTANCE_UNITS = (
        (METERS, 'meters'),
        (KILOMETERS, 'kilometers'),
        (MILES, 'miles'),
    )
    distance_units = models.CharField(max_length=2,
                                      choices=DISTANCE_UNITS,
                                      default=MILES)

    class Meta:
        unique_together = ('name', 'session',)


@receiver(pre_delete, sender=TimingSession,
          dispatch_uid="timingsession_pre_delete")
def delete_tag_times(sender, instance, using, **kwargs):
    """
    Delete all Split objects associated with this TimingSession prior to deletion.
    """
    instance.clear_results()


@receiver(post_delete, sender=Athlete, dispatch_uid='athlete_post_delete')
def delete_athlete_user(sender, instance, using, **kwargs):
    """
    Delete the user associated with an `Athlete`.
    """
    instance.user.delete()


@receiver(post_delete, sender=Coach, dispatch_uid='coach_post_delete')
def delete_coach_user(sender, instance, using, **kwargs):
    """
    Delete the user associated with a `Coach`.
    """
    instance.user.delete()


@receiver(m2m_changed, sender=Checkpoint.readers.through)
def verify_unique_reader_checkpoint(sender, **kwargs):
    """
    Verify that a reader can belong to no more than one checkpoint in a
    single session. See https://djangosnippets.org/snippets/2552/.
    """
    checkpoint = kwargs.get('instance', None)
    action = kwargs.get('action', None)
    readers = kwargs.get('pk_set', None)

    if action == 'pre_add':
        session = checkpoint.session
        for reader in readers:
            if session.checkpoint_set.exclude(id=checkpoint.id).filter(
                    readers=reader).exists():
                raise IntegrityError(
                    'Reader {} already exists in another checkpoint in '
                    'session {}'.format(reader, session.pk))
