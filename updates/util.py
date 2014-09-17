from django.core.exceptions import ObjectDoesNotExist
from common.models import Workout, Split, Tag, Reader
import datetime

def get_splits(w_num):
    """Returns a JSON object with current workout data, i.e, splits, names, etc."""
    wdata = {}
    try:
        w = Workout.objects.get(num=w_num)
    except ObjectDoesNotExist:
        return wdata

    wdata['date'] = w.start_time.strftime('%m.%d.%Y')
    wdata['workoutID'] = int(w_num)
    wdata['runners'] = []

    tag_ids = Split.objects.filter(workout_id=w_num).values_list('tag_id',
            flat=True).distinct()

    for tag_id in tag_ids:

        # Get the name of the tag's owner.
        user = Tag.objects.get(id=tag_id).user
        if user:
            name = user.first_name+' '+user.last_name
        else:
            name = str(tag_id)

        # Calculate the splits for this tag in the current workout.
        interval = []
        splits = Split.objects.filter(workout_id=w_num, tag_id=tag_id).order_by('time')
        for i in range(len(splits)-1):
            dt = splits[i+1].time-splits[i].time
            interval.append(dt.total_seconds())
        counter = range(1,len(interval)+1)    

        # Add the runner's data to the workout. 
        wdata['runners'].append({'name': name, 'counter': counter,
                                 'interval': interval})

    return wdata    

def parse_msg(string):
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
