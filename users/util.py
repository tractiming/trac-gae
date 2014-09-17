from django.contrib.auth.models import User, Group

def is_athlete(uname):
    if Group.objects.get(name='athletes').user_set.filter(
            username=uname).count():
        return True
    return False

def is_coach(uname):
    if Group.objects.get(name='coaches').user_set.filter(
            username=uname).count():
        return True
    return False

def user_type(user):
    if is_athlete(user):
        return 'athlete'
    elif is_coach(user):
        return 'coach'
    else:
        return 'user'
