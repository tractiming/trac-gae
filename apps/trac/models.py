from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.cache import cache
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from filters import filter_splits, get_sec_ms
from operator import itemgetter
from collections import namedtuple

class Tag(models.Model):
    """
    An RFID tag that is worn by an athlete.
    """
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, self.user.username if self.user else "")

    @property
    def uname(self):
        """The identifying name given to the tag's owner."""
        name = self.user.get_full_name()
        if name:
            return name
        else:
            return self.user.username

class Reader(models.Model):
    """
    An RFID reader that streams splits.
    """
    name = models.CharField(max_length=50,unique=True)
    id_str = models.CharField(max_length=50,unique=True)
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.name

    @property
    def active_sessions(self):
        """
        Returns a list of all active sessions the reader belongs to.
        """
        now = timezone.now()
        return self.timingsession_set.filter(start_time__lte=now, stop_time__gte=now)

class TagTime(models.Model):
    """
    A single split time from one tag.
    """
    tag = models.ForeignKey(Tag)
    time = models.DateTimeField()
    milliseconds = models.IntegerField()
    reader = models.ForeignKey(Reader)

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        return "time=%s, tag=%s" %(self.time, self.tag.id_str)

    @property
    def owner_name(self):
        name = self.tag.user.get_full_name()
        if not name:
            return ""
        return name

    @property
    def full_time(self):
        """Full time with milliseconds."""
        return (self.time.replace(microsecond=0)+
                timezone.timedelta(milliseconds=self.milliseconds))

class TimingSession(models.Model):
    """
    A collection of timing information, e.g. a workout or race.
    """
    name = models.CharField(max_length=50)
    manager = models.ForeignKey(User)
    readers = models.ManyToManyField(Reader)
    tagtimes = models.ManyToManyField(TagTime)
    
    start_time = models.DateTimeField(default=timezone.now, blank=True)
    stop_time = models.DateTimeField(default=timezone.now, blank=True)
    start_button_time = models.DateTimeField(blank=True, 
            default=timezone.datetime(1,1,1,1,1,1))
    registered_tags = models.ManyToManyField(Tag)

    comment = models.CharField(max_length=2500, null=True, blank=True)
    rest_time = models.IntegerField(default=0, blank=True)
    track_size = models.IntegerField(default=400, blank=True)
    interval_distance = models.IntegerField(default=200, blank=True)
    interval_number = models.IntegerField(default=0, blank=True)
    filter_choice = models.BooleanField(default=True)
    private = models.BooleanField(default=True)

    archived = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "num=%i, name=%s, start=%s" %(self.id, self.name, self.start_time)

    @property
    def num_tags(self):
        """Number of unique tags seen in this workout."""
        return self.tagtimes.values('tag_id').distinct().count()

    def sorted_tag_list(self, limit=None, offset=None):
        """Return IDs of all distinct tags seen in this workout.

        The tag IDs are ordered according to cumulative time (not factoring in
        milliseconds). Therefore, results calculated by iterating over the list
        of returned IDs will already be in order.

        """
        # The upper time bound is the most recent time seen.
        max_times = (self.tagtimes.values('tag_id').distinct()
                .annotate(time=models.Max('time'))[offset:limit])

        # The lower time bound is either the start button time or the oldest
        # time seen.
        if self.start_button_active():
            min_times = [{'time': self.start_button_time, 'tag_id': tid}
                         for tid in self.tagtimes.values_list('tag_id',
                             flat=True).distinct()[offset:limit]]
        else:
            min_times = (self.tagtimes.values('tag_id').distinct()
                .annotate(time=models.Min('time')))[offset:limit]

        diff = [(max_time['tag_id'], max_time['time']-min_time['time']) for
                max_time, min_time in zip(max_times, min_times)]
        sorted_times = sorted(diff, key=lambda x: x[1])

        return [t[0] for t in sorted_times]

    def is_active(self, time=None):
        """
        Returns True if the current time is between the start and stop times.
        """
        if time is None:
            current_time = timezone.now()
        else:
            current_time = time
        if (current_time > self.start_time) and (current_time < self.stop_time):
            return True
        return False

    def start_button_active(self):
        """
        Returns True if the start button has been triggered for the current
        workout, False otherwise.
        """
        return (self.start_button_time.year > 1)

    def start_button_reset(self):
        """
        Deactivate the start button by setting it to the default time.
        """
        self.start_button_time = timezone.datetime(1,1,1,1,1,1)
        self.save()

    def _calc_splits_by_tag(self, tag_id, filter_s=None, use_cache=True):
        """Calculate splits for a single tag.

        First try to read results from the cache. If results are not found, get
        the tag and all its times. Iterate through times to calculate splits.
        Save new (raw) results to cache. Apply filter at end. Note that
        filtered results are not actually cached.

        Args:
            tag_id (int): Unique tag ID.
            
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
            results = cache.get(('ts_%i_tag_%i_results' %(self.id, tag_id)))
        else:
            results = None

        Results = namedtuple('Results', 'user_id name team splits total')
        if not results:    
            tag = Tag.objects.get(id=tag_id)
            
            # Get the name of the tag's owner and their team.
            name = tag.user.get_full_name()
            if not name:
                name = tag.user.username
            #name = self.get_tag_name(tag_id)
            try:
                team = tag.user.groups.values_list('name', flat=True)[0]
            except:
                team = None

            # Filter times by tag id.
            times = self.tagtimes.filter(tag=tag).order_by('time')

            # Offset for start time if needed.
            if self.start_button_active():
                s_tt = TagTime(time=self.start_button_time, milliseconds=0)
                times = [s_tt]+list(times)
            
            # Calculate splits.
            interval = []
            for i in range(len(times)-1):
                dt = times[i+1].full_time-times[i].full_time
                interval.append(round(dt.total_seconds(), 3))

            results = (tag.user.id, name, team, interval)    
            
            # Save to the cache. Store the unfiltered results so that if the
            # filter choice is changed, we don't need to recalculate.
            if use_cache:
                cache.set(('ts_%i_tag_%i_results' %(self.id, tag_id)), results)   

        else:
            interval = results[-2]
        
        # Filtering algorithm.
        if filter_s is None:
            filter_s = self.filter_choice
        if filter_s:
            interval = filter_splits(results[-1], self.interval_distance, 
                                     self.track_size)

        return Results(results[0], results[1], results[2], interval, sum(interval))

    def _build_tag_archive(self):
        """
        Build the archive of tag-name relationships.
        """
        # If an archive already exists, delete it and create a new one.
        self._delete_tag_archive()
        tag_ids = self.tagtimes.values_list('tag_id',flat=True).distinct()
        for tid in tag_ids:
            tag = Tag.objects.get(id=tid)
            archived_tag = ArchivedTag.objects.create(id_str=tag.id_str,
                                                      username=tag.uname,
                                                      session_id=self.id)
            self.archivedtag_set.add(archived_tag)
        self.archived = True
        self.save()

    def _delete_tag_archive(self):
        """
        Destroy all archived tags in this workout.
        """
        self.archivedtag_set.all().delete()
        self.archived = False
        self.save()

    def get_tag_name(self, tag_id):
        """Get name of the person associated with a tag.

        Take into account archiving. Determine if an archive exists or should
        be built based on open/closed status of the workout and read from
        archive if one exists.

        """
        # If the workout is not active and archived, read from the saved names.
        if self.archived and (not self.is_active()):
            name_type = 'archived'

        # If the workout is closed but not archived, build the archive and read
        # from it.
        elif (not self.archived) and (not self.is_active()):
            self._build_tag_archive()
            name_type = 'archived'

        # If the workout is active and has an archive, delete the archive and
        # update the name dynamically. (This could occur if the workout is
        # reopened after it has already been closed.)
        elif self.archived and self.is_active():
            self._delete_tag_archive()
            name_type = 'current'

        # The final case is not archived and active. This case also dynamically
        # updates the name based on the current tag assignments.
        else:
            name_type = 'current'

        # Return either the archived or current name.
        tag = Tag.objects.get(id=tag_id)
        if name_type == 'archived':
            return self.archivedtag_set.filter(id_str=tag.id_str)[0].username

        else:
            return tag.uname
                
    def individual_results(self, limit=None, offset=None):
        """Calculate individual results for a session.

        First call `sorted_tag_list` for a list of tag IDs that are presorted
        by total time. Splice based on limit/offset and calc results one ID at
        a time.

        Args:
            limit (int|None): Max number of tags to return results for.
            offset (int|None): Offset when getting a subset of results.

        Returns:
            List of namedtuples of results.

        """
        all_tags = self.sorted_tag_list(limit, offset)
        results = [self._calc_splits_by_tag(tag_id) for tag_id in all_tags]
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
                            'id': Group.objects.get(name=team).id,
                            'name': team
                            }

        place = 1
        for athlete in individual_results:
            
            # Runners not on a team do not score or affect other scores.
            if athlete.team in scores:

                if len(scores[athlete.team]['athletes']) < num_scorers:
                    scores[athlete.team]['athletes'].append(athlete.name)
                    scores[athlete.team]['score'] += place

                place += 1

        teams_with_enough_runners = [scores[team] for team in scores if
                                     len(scores[team]['athletes']) == num_scorers]

        return  sorted(teams_with_enough_runners, key=lambda x: x['score'])


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
        tt = self.tagtimes.all()

        # Filter by gender.
        if gender:
            assert gender in ['M', 'F'], "Invalid gender."
            tt = tt.filter(tag__user__athlete__gender=gender)

        # Filter by age.
        if age_range:
            assert (age_range[0]<age_range[1])&(age_range[0]>=0), "Invalid age range"
            tt = tt.filter(tag__user__athlete__age__lte=age_range[1],
                           tag__user__athlete__age__gte=age_range[0])

        # Filter by team.
        if teams:
            tt = tt.filter(tag__user__groups__name__in=teams)

        all_tags = tt.values_list('tag_id', flat=True).distinct()
        results = [self._calc_splits_by_tag(tag_id) for tag_id in all_tags]
        return sorted(results, key=lambda x: x.total)

    def clear_results(self):
        """Remove all the tagtimes that currently exist in the session."""
        tag_ids = self.tagtimes.values_list('tag_id', flat=True).distinct()
        for tag_id in tag_ids:
            self.clear_cache(tag_id)
        self.tagtimes.clear()

    def clear_cache(self, tag_id):
        """Clear the session's cached results for a single tag."""
        cache.delete(('ts_%i_tag_%i_results' %(self.id, tag_id)))   

    def _delete_split(self, tag_id, split_indx):
        """
        Delete a result from the array of splits. The runner is identified by
        tag id and the split to be deleted is identified by its position in the
        array. The split index should refer to the position in the unfiltered 
        results.
        """
        assert self.filter_choice is False, "Filter must be off to delete."
        tt = TagTime.objects.filter(timingsession=self, tag__id=tag_id).order_by('time')

        # Find the index of the first tag time we need to change.
        if self.start_button_active():
            indx = split_indx
        else:
            indx = split_indx+1

        # Get the offset and delete the time.
        splits = self.calc_splits_by_tag(tag_id)
        off_sec, off_ms = get_sec_ms(splits[split_indx])
        offset = timezone.timedelta(seconds=off_sec, milliseconds=off_ms)
        tt[indx].delete()

        # Edit adjust the rest of the tagtimes to maintain the other splits.
        for i in range(indx, len(tt)):
            new = tt[i].full_time-offset
            tt[i].time = new
            tt[i].milliseconds = new.microsecond/1000
            tt[i].save()

    def _insert_split(self, tag_id, split_indx, val, shift):
        """
        Insert a new split into the array before the given index.
        Can specify whether to shift following splits.
        """
        assert self.filter_choice is False, "Filter must be off to insert."

        tt = TagTime.objects.filter(timingsession=self, tag__id=tag_id).order_by('time')
        sec, ms = get_sec_ms(val)
        split_dt = timezone.timedelta(seconds=sec, milliseconds=ms)

        # Find the index of the first tag time we need to change as well as the
        # previous (absolute) time.
        if self.start_button_active():
            indx = split_indx
            if indx == 0:
                t_prev = self.start_button_time
            else:
                t_prev = tt[indx-1].full_time
        else:
            indx = split_indx+1
            t_prev = tt[indx-1].full_time

        # Create a new tagtime.
        t_curr = t_prev+split_dt
        r = self.readers.all()[0]
        nt = TagTime.objects.create(tag_id=tag_id, time=t_curr,
                milliseconds=t_curr.microsecond/1000, reader=r)

        if shift:
            # Edit the rest of the tagtimes to maintain the other splits.
            for i in list(reversed(range(indx, len(tt)))):
                cur_tt = tt[i]
                new = cur_tt.full_time+split_dt
                cur_tt.time = new
                cur_tt.milliseconds = new.microsecond/1000
                cur_tt.save()

        # Add the new tagtime after the rest of the splits have already been
        # adjusted.
        self.tagtimes.add(nt.pk)
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

    def _overwrite_final_time(self, tag_id, hr, mn, sc, ms):
        """
        Force a final time for the given tag id. This will delete all existing
        splits and assign a final time only.
        """
        # Delete all existing times for this tag.
        times = TagTime.objects.filter(timingsession=self, tag__id=tag_id)

        first_tt = times[0]

        times.exclude(pk=times[0].pk).delete()

        # If the start button has not been set, we need to set it.
        #if not self.start_button_active():
        #    self.start_button_time = timezone.now()

        r = self.readers.all()[0]
        final_time = first_tt.full_time+timezone.timedelta(hours=hr, 
                                                   minutes=mn, seconds=sc)

        new_ms = first_tt.milliseconds + ms
        if new_ms > 999:
            final_time += timezone.timedelta(hours=0, minutes=0, seconds=1)
            new_ms = new_ms % 1000

        tt = TagTime.objects.create(tag_id=tag_id, reader=r, time=final_time,
                milliseconds=new_ms)
        self.tagtimes.add(tt.pk)
        self.save()

@receiver(pre_delete, sender=TimingSession, dispatch_uid="timingsession_pre_delete")
def delete_tag_times(sender, instance, using, **kwargs):
    """
    Delete all TagTime objects associated with this TimingSession prior to deletion.
    """
    instance.tagtimes.all().delete()

class AthleteProfile(models.Model):
    """
    An athlete is a type of user that owns tags and appears in workout
    results.
    """
    user = models.OneToOneField(User, related_name='athlete')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True)
    grade = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "name=%s" %self.user.username

    def get_completed_sessions(self):
        """Returns a list of sessions in which this user has participated."""
        return TimingSession.objects.filter(
                tagtimes__tag__user=self.user).distinct()
        
    def get_tags(self, json_data=True):
        """Returns a list of tags registered to the athlete."""
        tags = Tag.objects.filter(user=self.user)
        if not json_data:
            return tags
        ids = []
        for t in tags:
            ids.append(t.id_str)
        return {'count': len(ids), 'ids': ids}    

class CoachProfile(models.Model):
    """
    A coach is a type of user who is associated with a group of athletes,
    creates workouts, and owns readers.
    """
    user = models.OneToOneField(User, related_name='coach')
    organization = models.CharField(max_length=50)
    athletes = models.ManyToManyField(AthleteProfile)

    def __unicode__(self):
        return "name=%s" %self.user.username

class RaceDirectorProfile(models.Model):
    """
    A race director is a type of user.
    """
    user = models.OneToOneField(User)

class ArchivedTag(models.Model):
    """
    A record of a tag that saves the id and user's name. This is useful, for
    example, if a tag is reassigned to a new user. In that case, if an archive
    is not made, the results from previous workouts will be overwritten with
    the new tag owner's name.
    """
    id_str = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    session = models.ForeignKey(TimingSession)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, self.username)
