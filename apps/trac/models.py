from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
#import numpy
import time
import datetime
import decimal
THREEPLACES = (decimal.Decimal(10)**(-3))

class Tag(models.Model):
    """An RFID Tag. Has a name and belongs to one user."""
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User, unique=False, null=True, blank=True)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, 
                                  self.user.username if self.user else "")

class Reader(models.Model):
    """An RFID reader. Has an identifying number and can belong to many workouts."""
    name = models.CharField(max_length=50,unique=True)
    id_str = models.CharField(max_length=50,unique=True)
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.name

    @property
    def active_sessions(self):
        """Returns a list of all active sessions the reader belongs to."""
        now = timezone.now()
        return self.timingsession_set.filter(start_time__lte=now, stop_time__gte=now)

class TagTime(models.Model):
    """A single split time from one tag."""
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
    """A timing session, for example, a workout or race."""
    name = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    stop_time = models.DateTimeField()
    comment = models.CharField(max_length=2500,blank=True)
    rest_time = models.IntegerField()
    track_size = models.IntegerField()
    interval_distance = models.IntegerField()
    interval_number = models.IntegerField()
    filter_choice = models.BooleanField(default=True)
    manager = models.ForeignKey(User)
    readers = models.ManyToManyField(Reader)
    tagtimes = models.ManyToManyField(TagTime)
    
    def __unicode__(self):
        return "num=%i, start=%s" %(self.id, self.start_time)

    def is_active(self, time=None):
        """Returns True if the current time is between the start and stop times."""
        if time is None:
            current_time = timezone.now()
        else:
            current_time = time
        if (current_time > self.start_time) and (current_time < self.stop_time):
            return True
        return False

    def get_results(self, user=None, force_update=False):
        """Gets the current splits for the session."""
        
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
            interval = []
            filtered_interval = []
            statistics_interval = []
            
            #Determine Constant of impossible time for 400m off of distance
            if self.interval_distance <= 200:
				constant = 20
            elif self.interval_distance > 200 and self.interval_distance <= 300:
				constant = 30
            elif self.interval_distance > 300 and self.interval_distance <= 400:
				constant = 50
            elif self.interval_distance > 400 and self.interval_distance <= 800:
				constant = 52
            elif self.interval_distance > 800 and self.interval_distance <= 1200:
				constant = 55
            elif  self.interval_distance > 1200 and self.interval_distance <= 1600:
				constant = 58
            else:
				constant = 59
            #modify constant if on different sized track like 300m or 200m
            #Dont modify if 200s on 200m track
            if self.interval_distance >200:
				modified_constant = constant * (self.track_size/400.0)
            else:
				modified_constant = constant
				
            times = TagTime.objects.filter(timingsession=self, 
                                           tag=tag).order_by('time')
            #filtered option using constants
            for i in range(len(times)-1):
                t1 = times[i].time+timezone.timedelta(milliseconds=times[i].milliseconds)
                t2 = times[i+1].time+timezone.timedelta(milliseconds=times[i+1].milliseconds)
                dt = t2-t1
                if dt > datetime.timedelta(seconds=modified_constant):
					filtered_interval.append([float(decimal.Decimal(dt.total_seconds()).quantize(THREEPLACES))])
            filtered_counter = range(1,len(filtered_interval)+1)    
            
            # non filtered option
            for i in range(len(times)-1):
                t1 = times[i].time+timezone.timedelta(milliseconds=times[i].milliseconds)
                t2 = times[i+1].time+timezone.timedelta(milliseconds=times[i+1].milliseconds)
                dt = t2-t1
                interval.append([float(decimal.Decimal(dt.total_seconds()).quantize(THREEPLACES))])
                counter = range(1,len(interval)+1)   
            
            #mean = numpy.mean(interval)
            #std = numpy.std(interval)
			# statistics option
            #for i in range(len(times)-1):
			#	t1 = times[i].time+timezone.timedelta(milliseconds=times[i].milliseconds)
			#	t2 = times[i+1].time+timezone.timedelta(milliseconds=times[i+1].milliseconds)
			#	dt = t2-t1
			#	if dt > (datetime.timedelta(seconds=mean)-datetime.timedelta(seconds=(2*std))):
			#		statistics_interval.append([round(dt.total_seconds(), 3)])
           

            if self.filter_choice == True:
				wdata['runners'].append({'name': name, 'counter': filtered_counter,
                                     'interval': filtered_interval})
            else:
				# Add the runner's data to the workout. 
				wdata['runners'].append({'name': name, 'counter': counter,
                                     'interval': interval})
            

        return wdata    

    def get_athletes(self, names_only=True):
        """Returns a list of all users that are registered in the session."""
        user_list = []
        tag_ids = self.tagtimes.values_list('tag', flat=True).distinct()
        
        for tag_id in tag_ids:
            user = Tag.objects.get(id=tag_id).user
    
            if (user) and (user not in user_list):
                user_list.append(user)
        
        if not names_only:
            return user_list
        else:
            names = [u.username for u in user_list]
            return names

class AthleteProfile(models.Model):
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
    user = models.OneToOneField(User, related_name='coach')
    organization = models.CharField(max_length=50)
    athletes = models.ManyToManyField(AthleteProfile)

    def __unicode__(self):
        return "name=%s" %self.user.username

class RaceDirectorProfile(models.Model):
    user = models.OneToOneField(User)



