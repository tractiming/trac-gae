from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.cache import cache
from filters import filter_splits, get_sec_ms
from operator import itemgetter

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
        print self.timingsession_set.all()
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

    def calc_splits_by_tag(self, tag_id, filter_s=None):
        """
        Calculates the splits for a given tag in the current session.
        """
        # Filter times by tag id.
        tag = Tag.objects.get(id=tag_id)
        times = TagTime.objects.filter(timingsession=self, tag=tag).order_by('time')

        # Offset for start time if needed.
        if self.start_button_time.year > 1:
            s_tt = TagTime(time=self.start_button_time, milliseconds=0)
            times = [s_tt]+list(times)
        
        # Calculate splits.
        interval = []
        for i in range(len(times)-1):
            dt = times[i+1].full_time-times[i].full_time
            interval.append(round(dt.total_seconds(), 3))
        
        # Filtering algorithm.
        if filter_s is None:
            filter_s = self.filter_choice
        if filter_s:
            interval = filter_splits(interval, self.interval_distance, self.track_size)

        return interval

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
        """
        Returns the name of the person associated with the tag id. Will take
        into account archiving.
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
                
    def calc_results(self, tag_ids=None, read_cache=False, save_cache=False, m=0, n=1):
        """
        Calculates the raw results (user_id, user_name, team_name, splits,
        cumul_time). Can optionally filter by passing a list of tag ids to use.
        """
        # By default, use all tags in the workout.
        if tag_ids is None:
            tag_ids = self.tagtimes.values_list('tag_id',flat=True).distinct()

        # Try to read from the cache. Be careful using this. Reading from the
        # cache does not ensure the specified list of tag ids is being used.
        if read_cache:
            results = cache.get(('ts_%i_results' %self.id))
        else:
            results = None

        # Calculate the results.
        if not results:

            results = []
            for tag_id in tag_ids[m:n]:

                # Get the name of the tag's owner.
                name = self.get_tag_name(tag_id)
                user = Tag.objects.get(id=tag_id).user

                # Get the name of the user's team.
                try:
                    team = user.groups.values_list('name',flat=True)[0]
                except:
                    team = None

                # Get the splits and cumulative time.
                splits = self.calc_splits_by_tag(tag_id)
                cumul_time = sum(splits)

                # Compile the data.
                results.append((user.id, name, team, splits, cumul_time))

            # Sort by cumulative time.
            results.sort(key=itemgetter(4))

            # Save to the cache.
            if save_cache:
                cache.set(('ts_%i_results' %self.id), results)   
        return results

    def get_team_results(self, num_scorers=5):
        """Score team results. - basic implementation."""
        # Get all of the team names.
        results = self.calc_results(read_cache=True, save_cache=True)
        teams = set([r[2] for r in results if (r[2] is not None)])
        scores = dict(zip(teams, [[0,0] for i in range(len(teams))]))

        place = 1
        for athlete in results:
            if athlete[2] in teams:
                if scores[athlete[2]][0] < num_scorers:
                    scores[athlete[2]][0] += 1
                    scores[athlete[2]][1] += place
                place += 1    

        sorted_scores = sorted([(t, scores[t][1]) for t in scores if 
                         (scores[t][0]==num_scorers)], key=itemgetter(1))

        return [{'place': i+1, 
                 'name': sorted_scores[i][0], 
                 'score': sorted_scores[i][1]} for i in range(len(sorted_scores))]

    def get_filtered_results(self, gender='', age_range=[], teams=[]):
        """Gets a filtered list of tag ids."""
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

        tags = tt.values_list('tag_id',flat=True).distinct()
        res = self.calc_results(tag_ids=tags)
        
        res_dict = {'results': [{'name': res[i][1], 'place': i+1,
                                 'time': res[i][4] } for i in range(len(res))]}
        return res_dict

    def get_results(self, force_update=False, sort=False, m=0, n=1):
        """Get full results, formatted for mobile."""
        results = self.calc_results(read_cache=(not force_update), save_cache=True, m=m, n=n)
        if sort:
            results = sorted(sorted(results, key=lambda x: x[4]), reverse=True,
                    key=lambda x: len(x[3]))

        wdata = {}
        wdata['date'] = self.start_time.strftime('%m.%d.%Y')
        wdata['workoutID'] = self.id
        wdata['runners'] = [{'id': r[0],
                            'name': r[1], 
                            'counter': range(1,len(r[3])+1),
                            'interval': [[str(s)] for s in r[3]]} for r in results]

        return wdata

    def get_ordered_results(self, force_update=False):
        """Get the full results, ordered by cumulative time."""
        res =  self.get_results(force_update=force_update, sort=True)
        for r in res['runners']:
            r['interval'] = str(sum([float(t[0]) for t in r['interval']]))
        return res    

    def get_athlete_names(self):
        """
        Returns a list of all users that are registered in the session.
        """
        names = cache.get(('ts_%i_athlete_names' %self.id))

        if not names:
            names = []
            tag_ids = self.tagtimes.values_list('tag', flat=True).distinct()
            
            for tag_id in tag_ids:
                name = self.get_tag_name(tag_id)
    
                if name not in names:
                    names.append(name)
            
            cache.set(('ts_%i_athlete_names' %self.id), names)
        
        return names

    def clear_results(self):
        """Removes all the tagtimes that currently exist in the session."""
        self.tagtimes.clear()
        self.clear_cache()

    def clear_cache(self):
        """Clear the session's cached results."""
        cache.delete(('ts_%i_results' %self.id))
        cache.delete(('ts_%i_athlete_names' %self.id))

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

    def _insert_split(self, tag_id, split_indx, val):
        """
        Insert a new split into the array before the given index.
        """
        assert self.filter_choice is False, "Filter must be off to insert."
        tt = TagTime.objects.filter(timingsession=self, tag__id=tag_id).order_by('time')
        sec, ms = get_sec_ms(val)
        split_dt = timezone.timedelta(seconds=sec, milliseconds=ms)

        # Find the index of the first tag time we need to change as well as the
        # previous (absoulte) time.
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

        # Edit the rest of the tagtimes to maintain the other splits.
        for i in range(indx, len(tt)):
            new = tt[i].full_time+split_dt
            tt[i].time = new
            tt[i].milliseconds = new.microsecond/1000
            tt[i].save()

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
        self._insert_split(tag_id, split_indx, val)

    def _overwrite_final_time(self, tag_id, hr, mn, sc, ms):
        """
        Force a final time for the given tag id. This will delete all existing
        splits and assign a final time only.
        """
        # Delete all existing times for this tag.
        times = TagTime.objects.filter(timingsession=self, tag__id=tag_id)
        times.delete()

        # If the start button has not been set, we need to set it.
        if not self.start_button_active():
            self.start_button_time = timezone.now()

        r = self.readers.all()[0]
        final_time = self.start_button_time+timezone.timedelta(hours=hr, 
                                                    minutes=mn, seconds=sc) 
        tt = TagTime.objects.create(tag_id=tag_id, reader=r, time=final_time,
                milliseconds=ms)
        self.tagtimes.add(tt.pk)
        self.save()

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
