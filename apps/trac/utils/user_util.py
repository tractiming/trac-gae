import uuid


def is_athlete(user):
    """
    Returns True if the user is an athlete, False otherwise.
    """
    try:
        user.athlete
        return True
    except:
        return False

def is_coach(user):
    """
    Returns True if the user is a coach, False otherwise.
    """
    try:
        user.coach
        return True
    except:
        return False

def user_type(user):
    """
    Gives the type of user: coach, athlete, or generic user.
    """
    if is_athlete(user):
        return 'athlete'
    elif is_coach(user):
        return 'coach'
    else:
        return 'user'

def random_username():
    """Generate a random username."""
    return uuid.uuid4().hex[:30]  # Max 30 characters
