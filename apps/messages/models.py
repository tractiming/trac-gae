from django.core.validators import RegexValidator
from django.db import models

from trac.models import TimingSession, Athlete


class Subscriber(models.Model):
    """A subscriber is sent update messages that track an athlete in a
    session. A subscriber may be following multiple athletes in
    multiple sessions.
    """
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone_number = models.CharField(validators=[phone_regex], blank=True)
    sessions = models.ManyToManyField(TimingSession)
    athletes = models.ManyToManyField(Athlete)

    def __unicode__(self):
        return "phone={}".format(self.phone_number)


class Message(models.Model):
    """A message is a specific update sent to one subscriber at a
    particular time.
    """
    subscriber = models.ForeignKey(Subscriber)
    message = models.CharField(max_length=200)
    sent_time = models.DateTimeField()
    success = models.BooleanField()

    def __unicode__(self):
        if len(self.message) <= 15:
            text = self.message
        else:
            text = self.message[:11] + ' ...'
        return "phone={}, text={}, time={}".format(
            self.subscriber.phone_number, text, sent_time)
