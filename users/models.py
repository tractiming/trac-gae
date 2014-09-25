from django.db import models
from django.contrib.auth.models import User

class AthleteProfile(models.Model):
    user = models.OneToOneField(User)

class CoachProfile(models.Model):
    user = models.OneToOneField(User)
    organization = models.CharField(max_length=50)
    athletes = models.ManyToManyField(AthleteProfile)

class RaceDirectorProfile(models.Model):
    user = models.OneToOneField(User)

