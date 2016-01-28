from collections import namedtuple
import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models, connection
from django.db.models.signals import pre_delete, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from oauth2_provider.models import Application

from trac.utils.filter_util import get_filter_constant


def _upload_to(instance, filename):
    return '/'.join(('team-logo', instance.id, filename))


class Coach(models.Model):
    """
    A coach is a type of user who has a team of athletes, creates workouts,
    and owns readers.
    """
    user = models.OneToOneField(User)
    payment = models.CharField(max_length=25, null=True, blank=True)

    def __unicode__(self):
        return "name={}".format(self.user.username)


class Team(models.Model):
    """
    A team has one coach and many athletes.
    """
    name = models.CharField(max_length=50)
    coach = models.ForeignKey(Coach)
    tfrrs_code = models.CharField(max_length=20, unique=True, null=True,
                                  blank=True)
    primary_team = models.BooleanField(default=False)
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
    name = models.CharField(max_length=50, unique=True)
    id_str = models.CharField(max_length=50, unique=True)
    coach = models.ForeignKey(Coach)

    def __unicode__(self):
        return "id={}, name={}".format(self.id_str, self.name)

    @property
    def active_sessions(self):
        """
        Returns a list of all active sessions the reader belongs to.
        """
        return [session for session in TimingSession.objects.all() if
                session.active]


class Split(models.Model):
    """
    A single split time from one tag.
    """
    tag = models.ForeignKey(Tag, null=True, blank=True)
    athlete = models.ForeignKey(Athlete)
    reader = models.ForeignKey(Reader, null=True, blank=True)
    time = models.BigIntegerField()

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        tag = '' if self.tag is None else self.tag.id_str
        reader = '' if self.reader is None else self.reader.id_str
        return "time={}, tag={}, reader={}".format(
                self.time, tag, reader)


class TimingSession(models.Model):
    """
    A collection of timing information, e.g. a workout or race.
    """
    name = models.CharField(max_length=50)
    coach = models.ForeignKey(Coach)
    readers = models.ManyToManyField(Reader)
    splits = models.ManyToManyField(Split)

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

    def _sorted_athlete_list(self, limit=None, offset=None, gender=None,
                             age_lte=None, age_gte=None, teams=None):
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
        else:
            min_time = self.start_button_time

        results = self.splits.filter(athlete_filter).values(
            'athlete_id').annotate(diff=models.Max('time')-min_time).order_by(
            'diff')[offset:limit]

        return (athlete['athlete_id'] for athlete in results)

    def _calc_athlete_splits(self, athlete_id, filter_s=None, use_cache=True,
                             min_split=None):
        """Calculate splits for a single athlete.

        First try to read results from the cache. If results are not found, get
        the tag and all its times. Iterate through times to calculate splits.
        Save new (raw) results to cache. Apply filter at end. Note that
        filtered results are not actually cached.

        Returns namedtuple of (user id, name, team, splits, total_time)
        """
        # Try to read from the cache. Note that results are cached on a per tag
        # basis.
        if use_cache:
            results = cache.get(('ts_%i_athlete_%i_results'
                                 %(self.id, athlete_id)))
        else:
            results = None

        Results = namedtuple('Results', 'user_id name team splits total')
        if not results:
            athlete = Athlete.objects.get(id=athlete_id)
            name = athlete.user.get_full_name() or athlete.user.username

            times = list(self.splits.filter(athlete_id=athlete.id).order_by(
                'time').values_list('time', flat=True))

            # Offset for start time if needed.
            if self.start_button_time is not None:
                times.insert(0, self.start_button_time)

            interval = [round((t2 - t1)/1000.0, 3)
                        for t1, t2 in zip(times, times[1:])]
            results = (athlete_id, name, athlete.team, interval)

            # Save to the cache. Store the unfiltered results so that if the
            # filter choice is changed, we don't need to recalculate.
            if use_cache:
                cache.set(('ts_%i_athlete_%i_results' %(self.id, athlete_id)),
                          results)

        if min_split is not None:
            interval = filter(lambda x: x >= min_split, results[-1])
        else:
            interval = results[-1]

        return Results(results[0], results[1], results[2],
                       interval, sum(interval))

    def individual_results(self, limit=None, offset=None, gender=None,
                           age_lte=None, age_gte=None, teams=None,
                           apply_filter=None, athlete_ids=None):
        """Calculate individual results for a session.

        First call `_sorted_athlete_list` for a list of tag IDs that are
        presorted by total time. Splice based on limit/offset and calc
        results one ID at a time.

        If `athlete_ids` is given explicitly, calculate results for those
        athletes only. This option overrides any other filters or
        limit/offset.

        Individual results can also be filtered by age, gender, etc.
        """
        if athlete_ids is not None:
            athletes = list(set(athlete_ids))
        else:
            athletes = self._sorted_athlete_list(limit=limit,
                                                 offset=offset,
                                                 gender=gender,
                                                 age_lte=age_lte,
                                                 age_gte=age_gte,
                                                 teams=teams)

        if apply_filter is None:
            apply_filter = self.filter_choice
        if apply_filter:
            min_split = get_filter_constant(self.interval_distance,
                                            self.track_size)
        else:
            min_split = None

        return [self._calc_athlete_splits(athlete, min_split=min_split)
                for athlete in athletes]

    def team_results(self, num_scorers=5):
        """Calculate team scores.

        Compute the individual scores and compile a list of team names.
        Iterate through the runners and add their place to each team's score.
        """
        individual_results = self.individual_results()
        team_names = set([runner.team for runner in individual_results
                            if runner.team is not None])

        scores = {}
        for team in team_names:
            scores[team] = {
                'athletes': [],
                'score': 0,
                'id': team.id,
                'name': team.name
            }

        place = 1
        for athlete in individual_results:

            # Runners not on a team do not score or affect other scores.
            if athlete.team in scores:

                if len(scores[athlete.team]['athletes']) < num_scorers:
                    scores[athlete.team]['athletes'].append({
                        'name': athlete.name,
                        'place': place,
                        'total': athlete.total
                    })
                    scores[athlete.team]['score'] += place

                place += 1

        teams_with_enough_runners = (
                [scores[team] for team in scores if
                 len(scores[team]['athletes']) == num_scorers])

        return sorted(teams_with_enough_runners, key=lambda x: x['score'])

    def clear_results(self):
        """Remove all the splits that currently exist in the session."""
        athlete_ids = self.splits.values_list('athlete_id',
                                              flat=True).distinct()
        for athlete_id in athlete_ids:
            self.clear_cache(athlete_id)

        # Clear the link between split and session. Only delete the split if it
        # does not belong to any other sessions.
        self.splits.clear()
        Split.objects.filter(timingsession=None).delete()

    def clear_cache(self, athlete_id):
        """Clear the session's cached results for a single tag."""
        cache.delete(('ts_%i_athlete_%i_results' %(self.id, athlete_id)))



    # TODO: Move to utils.
    def _delete_split(self, athlete_id, split_indx):
        """
        Delete a result from the array of splits. The runner is identified by
        tag id and the split to be deleted is identified by its position in the
        array. The split index should refer to the position in the unfiltered
        results.
        """
        assert self.filter_choice is False, "Filter must be off to delete."
        tt = self.splits.filter(athlete_id=athlete_id).order_by('time')
        athlete = Athlete.objects.get(id=athlete_id)

        # Find the index of the first tag time we need to change.
        if self.start_button_time is not None:
            indx = split_indx
        else:
            indx = split_indx+1

        # Get the offset and delete the time.
        splits = self._calc_athlete_splits(athlete.id)
        offset_ms = int(splits[3][split_indx] * 1000)
        tt[indx].delete()

        # Edit the rest of the splits to maintain the other splits.
        for i in range(indx, len(tt)):
            tt[i].time = tt[i].time-offset_ms
            tt[i].save()

    # TODO: Move to utils.
    def _insert_split(self, athlete_id, split_indx, val, shift):
        """
        Insert a new split into the array before the given index.
        Can specify whether to shift following splits.
        """
        assert self.filter_choice is False, "Filter must be off to insert."

        tt = self.splits.filter(athlete_id=athlete_id).order_by('time')
        split_dt = val

        # Find the index of the first tag time we need to change as well as the
        # previous (absolute) time.
        if self.start_button_time is not None:
            indx = split_indx
            if indx == 0:
                t_prev = self.start_button_time
            else:
                t_prev = tt[indx-1].time
        else:
            indx = split_indx+1
            t_prev = tt[indx-1].time

        # Create a new tagtime.
        t_curr = t_prev+split_dt
        r = self.readers.all()[0]
        nt = Split.objects.create(athlete_id=athlete_id, time=t_curr,
                                  reader=r)

        if shift:
            # Edit the rest of the tagtimes to maintain the other splits.
            for i in list(reversed(range(indx, len(tt)))):
                cur_tt = tt[i]
                cur_tt.time = cur_tt.time+split_dt
                cur_tt.save()

        # Add the new tagtime after the rest of the splits have already been
        # adjusted.
        self.splits.add(nt.pk)
        self.save()

    # TODO: Move to utils.
    def _edit_split(self, athlete_id, split_indx, val):
        """
        Change the value of a split in the list of results. The split index
        should refer to the position in the unfiltered results.
        """
        assert self.filter_choice is False, "Filter must be off to edit."

        # The split is edited by deleting the current time and inserting a new
        # split in its place.
        self._delete_split(athlete_id, split_indx)
        self._insert_split(athlete_id, split_indx, val, True)

    # TODO: Move to utils.
    def _overwrite_final_time(self, athlete_id, hr, mn, sc, ms):
        """
        Force a final time for the given tag id. This will delete all existing
        splits and assign a final time only.
        """
        # Delete all existing times for this tag.
        times = self.splits.filter(athlete_id=athlete_id)
        times.delete()

        # If the start button has not been set, we need to set it.
        #if not self.start_button_active():
        #    self.start_button_time = timezone.now()

        r = self.readers.all()[0]
        final_time = self.start_button_time+(3600000*hr+60000*mn+1000*sc+ms)

        #if new_ms > 999:
        #    final_time += timezone.timedelta(hours=0, minutes=0, seconds=1)
        #    new_ms = new_ms % 1000

        tt = Split.objects.create(athlete_id=athlete_id, reader=r,
                                  time=final_time)
        self.splits.add(tt.pk)
        self.save()


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
