from django.db import models
from django.contrib.auth.models import User
from djangotoolbox.fields import ListField

class Athlete(models.Model):
    user = models.OneToOneField(User)

class Coach(models.Model):
    user = models.OneToOneField(User)
    organization = models.CharField(max_length=50)
    athletes = ListField(models.ForeignKey(Athlete))
    
class RaceDirector(models.Model):
    user = models.OneToOneField(User)

    
