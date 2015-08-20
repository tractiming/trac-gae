from django.db import models, connection 
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.cache import cache
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from filters import filter_splits, get_sec_ms
from operator import itemgetter
from collections import namedtuple
import datetime


class Coach(models.Model):
    """
    A coach is a type of user who has a team of athletes, creates workouts,
    and owns readers.
    """
    user = models.OneToOneField(User)
    payment = models.CharField(max_length=25, null=True, blank=True)

    def __unicode__(self):
        return "name=%s" %self.user.username


class Team(models.Model):
    """
    A team has one coach and many athletes.
    """
    name = models.CharField(max_length=50, unique=True)
    coach = models.ForeignKey(Coach)
    tfrrs_code = models.CharField(max_length=20, unique=True)

    def __unicode__(self):
        return "team_name=%s" %self.name


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
        return "name=%s" %self.user.username

    @property
    def age(self):
        """Athlete's current age (in years)."""
        if not self.birth_date:
            return None

        today = datetime.date.today()
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
    athlete = models.OneToOneField(Athlete)

    def __unicode__(self):
        return "id=%s, athlete=%s" %(self.id_str, self.athlete.user.username)


class Reader(models.Model):
    """
    An RFID reader that streams splits.
    """
    name = models.CharField(max_length=50, unique=True)
    id_str = models.CharField(max_length=50, unique=True)
    coach = models.ForeignKey(Coach)

    def __unicode__(self):
        return "id=%s, name=%s" %(self.id_str, self.name)

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
    tag = models.ForeignKey(Tag)
    athlete = models.ForeignKey(Athlete)
    reader = models.ForeignKey(Reader)
    time = models.BigIntegerField()

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        return "time=%s, tag=%s, reader=%s" %(self.time, self.tag.id_str,
                                              self.reader.id_str)


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
    registered_tags = models.ManyToManyField(Tag)
    use_registered_tags_only = models.BooleanField(default=False)
    private = models.BooleanField(default=True)

    comment = models.CharField(max_length=2500, blank=True)
    rest_time = models.IntegerField(default=0, blank=True)
    track_size = models.IntegerField(default=400, blank=True)
    interval_distance = models.IntegerField(default=200, blank=True)
    interval_number = models.IntegerField(default=0, blank=True)
    filter_choice = models.BooleanField(default=True)

    def __unicode__(self):
        return "num=%i, name=%s, coach=%s" %(self.id, self.name,
                                             self.coach.user.username)

    @property
    def num_athletes(self):
        """Number of unique athletes seen in this workout."""
        return self.splits.values('athlete_id').distinct().count()

    def sorted_athlete_list(self, limit, offset):
        """Return IDs of all distinct athletes seen in this workout.

        The athlete IDs are ordered according to cumulative time. Therefore,
        results calculated by iterating over the list of returned IDs will
        already be in order.

        """
        cursor = connection.cursor()

        if self.start_button_time is None:
            cursor.execute('''SELECT trac_split.id, trac_split.athlete_id,
                           trac_timingsession_splits.timingsession_id,
                           Max(trac_split.time)-Min(trac_split.time) as diff
                           FROM trac_split INNER JOIN trac_timingsession_splits
                           ON trac_split.id=trac_timingsession_splits.split_id
                           WHERE trac_timingsession_splits.timingsession_id=%s
                           GROUP BY trac_split.athlete_id ORDER BY diff
                           LIMIT %s,%s;''',
                           [self.id, offset, limit])
        else:
            cursor.execute('''SELECT trac_split.id, trac_split.athlete_id,
                           trac_timingsession_splits.timingsession_id AS ts_id,
                           Max(trac_split.time)-%s as diff
                           FROM trac_split INNER JOIN trac_timingsession_splits
                           ON trac_split.id=trac_timingsession_splits.split_id
                           WHERE trac_timingsession_splits.timingsession_id=%s
                           GROUP BY trac_split.athlete_id ORDER BY diff
                           LIMIT %s,%s;''',
                           [self.start_button_time, self.id, offset, limit])
        athlete_ids = [result[1] for result in cursor.fetchall()]
        cursor.close()
        return athlete_ids

    @property
    def active(self):
        """
        Returns True if the current time is between the start and stop times.
        """
        now = timezone.now()
        return ((now > self.start_time) and (now < self.stop_time))

    def calc_athlete_splits(self, athlete_id, filter_s=None, use_cache=True):
        """Calculate splits for a single athlete.

        First try to read results from the cache. If results are not found, get
        the tag and all its times. Iterate through times to calculate splits.
        Save new (raw) results to cache. Apply filter at end. Note that
        filtered results are not actually cached.

        Args:
            athlete_id (int): Unique athlete ID.
            
        Kwargs:
            filter_s (bool|True): Whether or not to filter splits.
            use_cache (bool|True): If True, will read/write results to/from
                cache.

        Returns:
            Namedtuple of (user id, name, team, splits, total_time)

        """
        # Try to read from the cache. Note that results are cached on a per tag
        # basis.
        if use_cache:
            results = cache.get(('ts_%i_athlete_%i_results' %(self.id, athlete_id)))
        else:
            results = None

        Results = namedtuple('Results', 'user_id name team splits total')
        if not results:    
            athlete = Athlete.objects.get(id=athlete_id)
            
            # Get the name of the tag's owner and their team.
            name = athlete.user.get_full_name()
            if not name:
                name = athlete.user.username
            
            # Filter times by tag id.
            times = self.splits.filter(athlete_id=athlete.id).order_by('time')

            # Offset for start time if needed.
            if self.start_button_time is not None:
                s_tt = Split(time=self.start_button_time)
                times = [s_tt]+list(times)
            
            # Calculate splits.
            interval = []
            for i in range(len(times)-1):
                dt = (times[i+1].time-times[i].time)/1000.0
                interval.append(round(dt, 3))

            results = (athlete_id, name, athlete.team, interval)    
            
            # Save to the cache. Store the unfiltered results so that if the
            # filter choice is changed, we don't need to recalculate.
            if use_cache:
                cache.set(('ts_%i_athlete_%i_results' %(self.id, athlete_id)),
                          results)   

        # Filtering algorithm.
        if filter_s is None:
            filter_s = self.filter_choice
        if filter_s:
            interval = filter_splits(results[-1], self.interval_distance, 
                                     self.track_size)
        else:
            interval = results[-1]

        return Results(results[0], results[1], results[2], interval, sum(interval))

    def individual_results(self, limit=10000000, offset=0):
        """Calculate individual results for a session.

        First call `sorted_athlete_list` for a list of tag IDs that are presorted
        by total time. Splice based on limit/offset and calc results one ID at
        a time.

        Args:
            limit (int|None): Max number of tags to return results for.
            offset (int|None): Offset when getting a subset of results.

        Returns:
            List of namedtuples of results.

        """
        all_athletes = self.sorted_athlete_list(limit, offset)
        results = [self.calc_athlete_splits(athlete_id) for athlete_id
                   in all_athletes]
        return results

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
            scores[team] = {'athletes': [],
                            'score': 0,
                            'id': team.id,
                            'name': team.name
                           }

        place = 1
        for athlete in individual_results:
            
            # Runners not on a team do not score or affect other scores.
            if athlete.team in scores:

                if len(scores[athlete.team]['athletes']) < num_scorers:
                    scores[athlete.team]['athletes'].append({'name': athlete.name, 
                                                             'place': place, 
                                                             'total': athlete.total})
                    scores[athlete.team]['score'] += place

                place += 1

        teams_with_enough_runners = [scores[team] for team in scores if
                                     len(scores[team]['athletes']) == num_scorers]

        return sorted(teams_with_enough_runners, key=lambda x: x['score'])

    def filtered_results(self, gender='', age_range=[], teams=[]):
        """Filter results by gender, age, or team.

        Note: this method does not support pagination.

        Kwargs:
            gender (str): Gender to filter by. (Should be 'M' or 'F'.)
            age_range (list): Upper and lower age bounds.
            teams (list): List of teams to give results for.

        Returns:
            List of namedtuples of results sorted by total time.
        
        """
        tt = self.splits.all()

        # Filter by gender.
        if gender:
            assert gender in ['M', 'F'], "Invalid gender."
            tt = tt.filter(athlete__gender=gender)

        # Filter by age.
        if age_range:
            assert (age_range[0]<age_range[1])&(age_range[0]>=0), "Invalid age range"
            now = timezone.now()
            birth_date_gte = now.replace(year=now.year-age_range[1])
            birth_date_lte = now.replace(year=now.year-age_range[0])

            tt = tt.filter(athlete__birth_date__lte=birth_date_lte,
                           athlete__birth_date__gte=birth_date_gte)

        # Filter by team.
        if teams:
            tt = tt.filter(athlete__team__name__in=teams)

        all_athletes = tt.values_list('athlete_id', flat=True).distinct()
        results = [self.calc_athlete_splits(athlete_id) for athlete_id in
                   all_athletes]
        return sorted(results, key=lambda x: x.total)

    def clear_results(self):
        """Remove all the splits that currently exist in the session."""
        athlete_ids = self.splits.values_list('athlete_id', flat=True).distinct()
        for athlete_id in athlete_ids:
            self.clear_cache(athlete_id)
        self.splits.all().delete()

    def clear_cache(self, athlete_id):
        """Clear the session's cached results for a single tag."""
        cache.delete(('ts_%i_athlete_%i_results' %(self.id, athlete_id)))   

    def _delete_split(self, tag_id, split_indx):
        """
        Delete a result from the array of splits. The runner is identified by
        tag id and the split to be deleted is identified by its position in the
        array. The split index should refer to the position in the unfiltered 
        results.
        """
        assert self.filter_choice is False, "Filter must be off to delete."
        tt = self.splits.filter(tag__id=tag_id).order_by('time')
        athlete = Athlete.objects.get(tag__id=tag_id)

        # Find the index of the first tag time we need to change.
        if self.start_button_time is not None:
            indx = split_indx
        else:
            indx = split_indx+1

        # Get the offset and delete the time.
        splits = self.calc_athlete_splits(athlete.id)
        offset_ms = int(splits[3][split_indx] * 1000)
        tt[indx].delete()

        # Edit the rest of the splits to maintain the other splits.
        for i in range(indx, len(tt)):
            tt[i].time = tt[i].time-offset_ms
            tt[i].save()

    def _insert_split(self, tag_id, split_indx, val, shift):
        """
        Insert a new split into the array before the given index.
        Can specify whether to shift following splits.
        """
        assert self.filter_choice is False, "Filter must be off to insert."

        tt = self.splits.filter(tag__id=tag_id).order_by('time')
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
        athlete = Athlete.objects.get(tag__id=tag_id)
        nt = Split.objects.create(tag_id=tag_id, athlete=athlete, time=t_curr, reader=r)

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

    def _edit_split(self, tag_id, split_indx, val):
        """
        Change the value of a split in the list of results. The split index
        should refer to the position in the unfiltered results. 
        """
        assert self.filter_choice is False, "Filter must be off to edit."

        # The split is edited by deleting the current time and inserting a new
        # split in its place.
        self._delete_split(tag_id, split_indx)
        self._insert_split(tag_id, split_indx, val, True)

    # FIXME
    def _overwrite_final_time(self, tag_id, hr, mn, sc, ms):
        """
        Force a final time for the given tag id. This will delete all existing
        splits and assign a final time only.
        """
        # Delete all existing times for this tag.
        times = self.splits.filter(tag__id=tag_id)
        times.delete()

        # If the start button has not been set, we need to set it.
        #if not self.start_button_active():
        #    self.start_button_time = timezone.now()

        r = self.readers.all()[0]
        final_time = self.start_button_time+(3600000*hr+60000*mn+1000*sc+ms)

        #if new_ms > 999:
        #    final_time += timezone.timedelta(hours=0, minutes=0, seconds=1)
        #    new_ms = new_ms % 1000

        athlete = Athlete.objects.get(tag__id=tag_id)
        tt = Split.objects.create(tag_id=tag_id, athlete=athlete, reader=r, time=final_time)
        self.splits.add(tt.pk)
        self.save()

@receiver(pre_delete, sender=TimingSession, dispatch_uid="timingsession_pre_delete")
def delete_tag_times(sender, instance, using, **kwargs):
    """
    Delete all Split objects associated with this TimingSession prior to deletion.
    """
    instance.splits.all().delete()


class PerformanceRecord(models.Model):
    distance = models.IntegerField()
    time = models.FloatField()
    interval = models.CharField(max_length=1)
    VO2 = models.IntegerField(null=True, blank=True)
    athlete = models.ForeignKey(Athlete, null=True)
    coach = models.ForeignKey(Coach, null=True)

    def __unicode__(self):
        if self.athlete:
            name = self.athlete.user.username
        elif self.coach:
            name = self.coach.user.username
        else:
            name = ''
        return "user=%s distance=%i time=%.3f" %(name, self.distance, self.time)
