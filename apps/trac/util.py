from django.core.exceptions import ObjectDoesNotExist
from models import TimingSession, TagTime, Tag, Reader
import datetime
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

def parse_raw_msg(string):
    """Extracts split data from reader notification message."""
    # Check that tag contains good information.
    if ('Tag:' not in string) or ('Last:' not in string) or ('Ant:' not in string):
        return None

    msg_info = {}
    for d in string.split(', '):
        k = d.split(':')
        
        if k[0] == 'Tag':
            msg_info['name'] = k[1]
        elif k[0] == 'Last':
            time_str = d[5:]
            msg_info['time'] = datetime.datetime.strptime(time_str,
                                                          "%Y/%m/%d %H:%M:%S.%f") 
        elif k[0] == 'Ant':
            msg_info['Ant'] = int(k[1])

    return msg_info

def parse_formatted_msg(msg):
    """Extracts time data from a formatted reader message."""
    for token in ['ant', 'r', 'id', 'time']:
        if token not in msg:
            return None
    
    msg_info = {'name': msg['ant'] 
            }
    
