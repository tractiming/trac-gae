from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.cache import cache
from util import filter_splits
from operator import itemgetter

class Tag(models.Model):
    """
    An RFID tag that is worn by an athlete.
    """
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, self.user.username if self.user else "")

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
    
    #number_scoring=models.IntegerField(default=5)
    #gender_scoring=models.CharField(max_length=50,blank=True,default='male')
    #age_scoring=JSONField(blank=True,default={})
    #grade_scoring=JSONField(max_length=50,blank=True,default={})

    def __unicode__(self):
        return "num=%i, start=%s" %(self.id, self.start_time)

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
            t1 = times[i].time+timezone.timedelta(
                    milliseconds=times[i].milliseconds)
            t2 = times[i+1].time+timezone.timedelta(
                    milliseconds=times[i+1].milliseconds)
            dt = t2-t1
            interval.append(round(dt.total_seconds(), 3))
        
        # Filtering algorithm.
        if filter_s is None:
            filter_s = self.filter_choice
        if filter_s:
            interval = filter_splits(interval, self.interval_distance, self.track_size)

        return interval

    def calc_results(self, tag_ids=[], read_cache=False, save_cache=False):
        """
        Calculates the raw results (user_id, user_name, team_name, splits,
        cumul_time). Can optionally filter by passing a list of tag ids to use.
        """
        
        # By default, use all tags in the workout.
        if not tag_ids:
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
            for tag_id in tag_ids:

                # Get the name of the tag's owner.
                tag = Tag.objects.get(id=tag_id)
                user = tag.user
                if user:
                    name = user.get_full_name()
                    if not name:
                        name = user.username
                else:
                    name = str(tag_id)
                
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
        scores = dict(zip(teams, [[0,0]]*len(teams)))

        place = 1
        for athlete in results:
            if athlete[2] in teams:
                if scores[athlete[2]] < num_scorers:
                    scores[athlete[2]][0] += 1
                    scores[athlete[2]][1] += place
                place += 1    

        return scores

    def get_filtered_results(self, teams=[], genders=[], age_ranges=[], grades=[]):
        """Gets a filtered list of tag ids."""
        q_obj = models.Q()
        
        # Filter by gender.
        if genders:
            gd = models.Q()
            for gender in genders:
                gd |= models.Q(tag__user__athlete__gender=gender)
            q_obj &= gd    

        # Filter by grade.
        if grades:
            gr = models.Q()
            for grade in grades:
                gr |= models.Q(tag__user__athlete__grade=grade)
            q_obj &= gr   

        # Filter by age.
        if age_ranges:
            ag = models.Q()
            for age_range in age_ranges:
                ag |= (models.Q(tag__user__athlete__age__lte=age_range[1]) &
                       models.Q(tag__user__athlete__age__gte=age_range[0]))
            q_obj &= ag    
       
        # Filter by team.
        if teams:
            q_obj &= models.Q(tag__user__groups__name__in=teams)

        tags = self.tagtimes.filter(q_obj).values_list('tag_id',flat=True).distinct()
        return self.calc_results(tag_ids=tags)

    def get_results(self, force_update=False):
        """Get full results, formatted for mobile."""
        results = self.calc_results(read_cache=(not force_update), save_cache=True)
        wdata = {}
        wdata['date'] = self.start_time.strftime('%m.%d.%Y')
        wdata['workoutID'] = self.id
        wdata['runners'] = [{'name': r[1], 'counter': range(1,len(r[3])+1),
                            'interval': [[str(s)] for s in r[3]]} for r in results]
        return wdata
    
    def get_score(self):
		"""
		Calculate score from data fed from get_final_results
		"""
		scored_array=[]
		schools = []
		scoring_runners=[]
		score_breakdown=[]
		score=[]
		#compare registered schools to schools of runners
		for t in self.participating_schools:
			count=0
			points = 0
			r = 0
			team_scorers=[]
			team_score_breakdown=[]
			while r<len(self.sorted_results[0]) and count < self.number_scoring: #change to scoring_runners
				
				if(self.sorted_results[0][r][2] == t):
				    count = count + 1
				    points = points + r + 1
				    team_scorers.append(self.sorted_results[0][r][1])
				    team_score_breakdown.append(r+1)
				r = r + 1
			#compare team to scoring standard, if less than standard set to null	
			if count < self.number_scoring:#change to scoring_runners
				points= None
			
            # if we need individual arrays,or json format will need to redo and
            # order json
			score_breakdown.append(team_score_breakdown)	
			scoring_runners.append(team_scorers)
			scored_array.append(points)
			schools.append(t)
            #score.append({'team': team_score_breakdown, 'team scoreres':
            #team_scorers, 'points': points,'school':t})
			
		zipped_scores = [sorted(zip(scored_array,schools,scoring_runners,score_breakdown))]
		return zipped_scores


    def get_athlete_names(self):
        """
        Returns a list of all users that are registered in the session.
        """
        names = cache.get(('ts_%i_athlete_names' %self.id))

        if not names:
            user_list = []
            tag_ids = self.tagtimes.values_list('tag', flat=True).distinct()
            
            for tag_id in tag_ids:
                user = Tag.objects.get(id=tag_id).user
        
                if (user) and (user not in user_list):
                    user_list.append(user)
            
            names = [u.username for u in user_list]
            cache.set(('ts_%i_athlete_names' %self.id), names)
        
        return names

    def clear_results(self):
        """Removes all the tagtimes that currently exist in the session."""
        self.tagtimes.clear()
        cache.delete(('ts_%i_results' %self.id))
        cache.delete(('ts_%i_athlete_names' %self.id))

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

'''
    def get_final_results(self, user=None, force_update=False):
        """Gets the current splits for the session."""
        
        wdata = cache.get(('ts_%i_results' %self.id))

        if not wdata:
            name_array = []
            time_array=[]
            school = []
            q_objects=Q()
            
            #Filter by gender, age, grade. Note that age and grade are json arrays
            #TODO: Filter by team
            			
            if self.age_scoring:
			    for age in self.age_scoring:
				    q_objects |= Q(tag__user__athlete__age=age)
			
            if self.grade_scoring:
			    for grade in self.grade_scoring:
				    q_objects |= Q(tag__user__athlete__grade=grade)
		    
            if self.gender_scoring:
				q_objects &= Q(tag__user__athlete__gender=self.gender_scoring)
			
				
            tag_ids = self.tagtimes.filter(q_objects).values_list('tag_id',flat=True).distinct()
            for tag_id in tag_ids:

                # Get the name of the tag's owner.
                tag = Tag.objects.get(id=tag_id)
                user = tag.user
                if user:
                    name = user.get_full_name()
                    if not name:
                        name = user.username
                else:
                    name = str(tag_id)
                
                try:
                    team = user.groups.values_list('name',flat=True)[0]
                except:
                    team = None
                
                # Calculate the splits for this tag in the current workout.
                times = TagTime.objects.filter(timingsession=self, 
                                               tag=tag).order_by('time')
                
                interval = []
                scoring_time = []
                for i in range(len(times)-1):
                    t1 = times[i].time+timezone.timedelta(
                            milliseconds=times[i].milliseconds)
                    t2 = times[i+1].time+timezone.timedelta(
                            milliseconds=times[i+1].milliseconds)
                    dt = t2-t1

                    # Convert the number to a string to prevent round-off error.
                    str_dt = str(round(dt.total_seconds(), 3))
                    interval.append([str_dt])
                    scoring_time.append(round(dt.total_seconds(), 3))

                counter = range(1,len(interval)+1)   

                # Filtering algorithm.
                if self.filter_choice:
                    interval, counter = filter_splits(interval, 
                                                      self.interval_distance,
                                                      self.track_size)

                # Add the runner's data to the workout. 
                #Insure that scoring_time[-1] is the same array length if reader misses runner

                name_array.append(name)
                time_array.append(scoring_time[-1])
                school.append(team)
        
        #TODO: Better JSON Sorted by time?
        self.participating_schools = set(school)   
        #sort arrays by fastest time, print name and time in order
        sorted_results = [sorted(zip(time_array,name_array,school))]
        self.sorted_results = sorted_results
        return (sorted_results)
    def get_results_old(self, force_update=False):
        """
        Gets the current splits for the session. The force_update argument
        ensures splits are recalculated and not read from cache.
        """
        wdata = cache.get(('ts_%i_results' %self.id))

        if (not wdata) or (force_update):
            wdata = {}
            wdata['date'] = self.start_time.strftime('%m.%d.%Y')
            wdata['workoutID'] = self.id
            wdata['runners'] = []

            tag_ids = self.tagtimes.values_list('tag_id',flat=True).distinct()
            for tag_id in tag_ids:

                # Get the name of the tag's owner.
                tag = Tag.objects.get(id=tag_id)
                user = tag.user
                if user:
                    name = user.get_full_name()
                    if not name:
                        name = user.username
                else:
                    name = str(tag_id)

                # Calculate the splits for this tag in the current workout.
                times = TagTime.objects.filter(timingsession=self, 
                                               tag=tag).order_by('time')
                if self.start_button_time.year > 1:
                    s_tt = TagTime(time=self.start_button_time, milliseconds=0)
                    times = [s_tt]+list(times)
                
                interval = []
                for i in range(len(times)-1):
                    t1 = times[i].time+timezone.timedelta(
                            milliseconds=times[i].milliseconds)
                    t2 = times[i+1].time+timezone.timedelta(
                            milliseconds=times[i+1].milliseconds)
                    dt = t2-t1

                    # Convert the number to a string to prevent round-off error.
                    str_dt = str(round(dt.total_seconds(), 3))
                    interval.append([str_dt])

                counter = range(1,len(interval)+1)   

                # Filtering algorithm.
                if self.filter_choice:
                    interval, counter = filter_splits(interval, 
                                                      self.interval_distance,
                                                      self.track_size)

                # Add the runner's data to the workout. 
                wdata['runners'].append({'name': name, 'counter': counter,
                             'interval': interval})

            cache.set(('ts_%i_results' %self.id), wdata)    

        return wdata    
'''
