from django.contrib.auth.models import User
from django.db import models


class GoogleSignIn(models.Model):
    """Credentials linking a user to a Google ID."""
    google_id = models.CharField(unique=True, max_length=50)
    user = models.OneToOneField(User)

    def __unicode__(self):
        return "username={}, id={}".format(self.user.username,
                                           self.google_id)
