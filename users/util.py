from django.contrib.auth.models import User, Group

def is_athlete(user):
    try:
        user.athlete_profile
        return True
    except:
        return False

def is_coach(uname):
    try:
        user.coach_profile
        return True
    except:
        return False

def user_type(user):
    if is_athlete(user):
        return 'athlete'
    elif is_coach(user):
        return 'coach'
    else:
        return 'user'
