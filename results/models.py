from django.db import models
from django.contrib.auth.models import User
from common.models import TimingSession


class SessionLog(models.Model):
    """A workout log is a workout with additional information."""
    session = models.ForeignKey(TimingSession)
    owner = models.ForeignKey(User)
    comments = models.CharField(max_length=250)
