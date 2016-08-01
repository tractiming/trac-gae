from django.db import models
from trac.models import Athlete, Coach

class PerformanceRecord(models.Model):
    distance = models.IntegerField()
    time = models.FloatField()
    interval = models.CharField(max_length=1)
    VO2 = models.FloatField(null=True, blank=True)
    athlete = models.ForeignKey(Athlete, null=True)
    coach = models.ForeignKey(Coach, null=True)
    date = models.DateTimeField(null=True)
    event_name = models.CharField(max_length=100)

    def __unicode__(self):
        if self.athlete:
            name = self.athlete.user.username
        elif self.coach:
            name = self.coach.user.username
        else:
            name = ''
        return "user={}".format(name)
