from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Tag(models.Model):
    """An RFID Tag. Has a name and belongs to one user."""
    id_str = models.CharField(max_length=50)
    user = models.ForeignKey(User, unique=True, null=True, blank=True)

    def __unicode__(self):
        return self.id_str

class Workout(models.Model):
    """A workout session. Has start and stop time."""
    start_time = models.DateTimeField()
    stop_time = models.DateTimeField()
    owner = models.ForeignKey(User)

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

    def all_users(self):
        """Returns a list of all users that are registered in the workout."""
        user_list = []
        tag_ids = self.split_set.values_list('tag', flat=True).distinct()
        for tag_id in tag_ids:
            user = Tag.objects.get(id=tag_id).user

            if (user) and (user not in user_list):
                user_list.append(user)

        return user_list        

class Reader(models.Model):
    """An RFID reader. Has an identifying number and can belong to many workouts."""
    num = models.IntegerField(default=0)
    workouts = models.ManyToManyField(Workout)
    owner = models.ForeignKey(User)
    key = models.CharField(max_length=50)

    def __unicode__(self):
        return "%i" %self.num

    def active_workouts(self):
        """Returns a list of active workouts to which reader belongs."""
        return [w for w in self.workouts.all() if w.is_active()]

class Split(models.Model):
    """A single split time from one tag."""
    tag = models.ForeignKey(Tag)
    time = models.DateTimeField()
    reader = models.ForeignKey(Reader)
    workout = models.ForeignKey(Workout)

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        return "time=%s, tag=%s, reader=%i" %(self.time, self.tag.id_str, self.reader.num)


    def parent_workout(self):
        """Gets the parent workout for a single split."""
        return self.reader.workouts.filter(start_time__lt=self.time, 
                                           stop_time__gt=self.time)[0]

