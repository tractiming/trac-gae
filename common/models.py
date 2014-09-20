from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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

class TimingSession(models.Model):
    """A timing session, for example, a workout or race."""
    name = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    stop_time = models.DateTimeField()
    manager = models.ForeignKey(User)
    readers = models.ManyToManyField(Reader)

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

    #def all_users(self):
    #    """Returns a list of all users that are registered in the session."""
    #    user_list = []
    #    tag_ids = self.split_set.values_list('tag', flat=True).distinct()
    #    for tag_id in tag_ids:
    #        user = Tag.objects.get(id=tag_id).user
    #
    #        if (user) and (user not in user_list):
    #            user_list.append(user)
    #
    #    return user_list        


class TagTime(models.Model):
    """A single split time from one tag."""
    tag = models.ForeignKey(Tag)
    time = models.DateTimeField()
    reader = models.ForeignKey(Reader)
    session = models.ForeignKey(TimingSession)

    class Meta:
        unique_together = ("tag", "time",)

    def __unicode__(self):
        return "time=%s, tag=%s, reader=%s" %(self.time, self.tag.id_str, 
                                              self.reader.id_str)


