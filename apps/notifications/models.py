from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from twilio.rest import TwilioRestClient

from trac.models import TimingSession, Athlete


class Subscription(models.Model):
    """A subscription defines when and where update messages are sent.
    A subscription covers one athlete in one session.
    """
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone_number = models.CharField(max_length=17, validators=[phone_regex],
                                    blank=True)
    session = models.ForeignKey(TimingSession)
    athlete = models.ForeignKey(Athlete)

    def __unicode__(self):
        return "phone={}, athlete={}, session={}".format(
            self.phone_number, self.athlete.pk, self.session.pk)


class Message(models.Model):
    """A message is a specific update sent to one subscriber at a
    particular time.
    """
    subscription = models.ForeignKey(Subscription)
    message = models.CharField(max_length=200)
    sent_time = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        if len(self.message) <= 15:
            text = self.message
        else:
            text = self.message[:11] + ' ...'
        return "phone={}, text='{}', time={}".format(
            self.subscription.phone_number, text, self.sent_time)

    def send(self):
        """Send an SMS notification with this message."""
        client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID,
                                  settings.TWILIO_AUTH_TOKEN)
        resp = client.messages.create(to=self.subscription.phone_number,
                                      from_=settings.TWILIO_PHONE_NUMBER,
                                      body=self.message)
        self.sent_time = timezone.now()
        return resp
