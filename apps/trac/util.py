from django.contrib.auth.models import User, Group

def is_athlete(user):
    """Checks if the user is an athlete."""
    try:
        user.athleteprofile
        return True
    except:
        return False

def is_coach(user):
    """Checks if the user is a coach."""
    try:
        user.coachprofile
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
