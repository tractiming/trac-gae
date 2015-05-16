from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
import time
import datetime
from util import filter_splits
import numpy
import datetime
from django.db import models
from jsonfield import JSONField

class Tag(models.Model):
    """
    An RFID Tag. Has a name and belongs to one user.
    """
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, 
                                  self.user.username if self.user else "")

class Reader(models.Model):
    """
    An RFID reader. Has an identifying number and belongs to one user.
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
            return "Unknown"
        return name

class TimingSession(models.Model):
    """
    A timing session is, for example, a workout or race.
    """
    name = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    stop_time = models.DateTimeField()
    manager = models.ForeignKey(User)
    readers = models.ManyToManyField(Reader)
    tagtimes = models.ManyToManyField(TagTime)

    comment = models.CharField(max_length=2500,blank=True)
    rest_time = models.IntegerField()
    track_size = models.IntegerField()
    interval_distance = models.IntegerField()
    interval_number = models.IntegerField()
    filter_choice = models.BooleanField(default=True)
    private = models.BooleanField(default=True)
    number_scoring=models.IntegerField(default=5)
    gender_scoring=models.CharField(max_length=50,blank=True,default='male')
    age_scoring=JSONField(blank=True,default={})
    grade_scoring=JSONField(max_length=50,blank=True,default={})

    start_button_time = models.DateTimeField(default=timezone.datetime(1,1,1,1,1,1))
    registered_tags = models.ManyToManyField(Tag)
    
    def __unicode__(self):
        return "num=%i, start=%s, gender=%i, age=%i,grade=%i,scoring=%i" %(self.id, self.start_time,self.gender_scoring,self.age_scoring,self.grade_scoringself.number_scoring)

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
			
			# if we need individual arrays,or json format will need to redo and order json
			score_breakdown.append(team_score_breakdown)	
			scoring_runners.append(team_scorers)
			scored_array.append(points)
			schools.append(t)
			#score.append({'team': team_score_breakdown, 'team scoreres': team_scorers, 'points': points,'school':t})
			
		zipped_scores = [sorted(zip(scored_array,schools,scoring_runners,score_breakdown))]
		return zipped_scores
    
    def get_results(self, force_update=False):
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
        return

class AthleteProfile(models.Model):
    """
    An athlete is a type of user that owns tags and appears in workout
    results.
    """
    user = models.OneToOneField(User, related_name='athlete')

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

