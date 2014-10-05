from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Tag(models.Model):
    """An RFID Tag. Has a name and belongs to one user."""
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User, unique=True, null=True, blank=True)

    def __unicode__(self):
        return "id=%s, user=%s" %(self.id_str, 
                                  self.user.username if self.user else "")

class Reader(models.Model):
    """An RFID reader. Has an identifying number and can belong to many workouts."""
    name = models.CharField(max_length=50)
    id_str = models.CharField(max_length=50)
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

    def results(self, force_update=False):
        """Gets the current splits for the session."""
        
        wdata['date'] = self.start_time.strftime('%m.%d.%Y')
        wdata['workoutID'] = self.id
        wdata['runners'] = []

        tag_ids = self.tagtimes.values_list('tag_id',flat=True).distinct()

        for tag_id in tag_ids:

            # Get the name of the tag's owner.
            user = Tag.objects.get(id=tag_id).user
            if user:
                name = user.get_full_name()
            else:
                name = str(tag_id)

            # Calculate the splits for this tag in the current workout.
            interval = []
            times = TagTime.objects.filter(timingsession_id=snum, 
                                           tag_id=tag_id).order_by('time')
            for i in range(len(splits)-1):
                dt = times[i+1].time-times[i].time
                interval.append(dt.total_seconds())
            counter = range(1,len(interval)+1)    

            # Add the runner's data to the workout. 
            sdata['runners'].append({'name': name, 'counter': counter,
                                     'interval': interval})

        return sdata    

    def all_users(self):
        """Returns a list of all users that are registered in the session."""
        user_list = []
        tag_ids = self.tagtimes.values_list('tag', flat=True).distinct()
        
        for tag_id in tag_ids:
            user = Tag.objects.get(id=tag_id).user
    
            if (user) and (user not in user_list):
                user_list.append(user)
   
        return user_list        




