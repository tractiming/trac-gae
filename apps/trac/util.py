from django.utils import timezone

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

def filter_splits(unfiltered_splits, interval_distance, track_size):    
    """
    Filters splits based on interval type and track size.
    """
    # Determine constant of impossible time for 400m off of distance.
    if interval_distance <= 200:
        constant = 20
    elif interval_distance > 200 and interval_distance <= 300:
        constant = 30
    elif interval_distance > 300 and interval_distance <= 400:
        constant = 50
    elif interval_distance > 400 and interval_distance <= 800:
        constant = 52
    elif interval_distance > 800 and interval_distance <= 1200:
        constant = 55
    elif  interval_distance > 1200 and interval_distance <= 1600:
        constant = 58
    else:
        constant = 59

    # Modify constant if on different sized track like 300m or 200m.
    # (Don't modify if 200s on 200m track.)
    if interval_distance >200:
        modified_constant = constant * (track_size/400.0)
    else:
        modified_constant = constant

    dt_sec = timezone.timedelta(seconds=modified_constant).total_seconds()
    filtered_interval = [dt for dt in unfiltered_splits if dt>dt_sec]    
    #filtered_counter = range(1,len(filtered_interval)+1)    
    
    return filtered_interval#, filtered_counter
       
