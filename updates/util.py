from django.core.exceptions import ObjectDoesNotExist
from common.models import TimingSession, TagTime, Tag, Reader
import datetime

def get_splits(snum):
    """Returns a JSON object with current workout data, i.e, splits, names, etc."""
    sdata = {}
    try:
        s = TimingSession.objects.get(pk=snum)
    except ObjectDoesNotExist:
        return sdata

    wdata['date'] = s.start_time.strftime('%m.%d.%Y')
    wdata['workoutID'] = int(snum)
    wdata['runners'] = []

    tag_ids = TagTime.objects.filter(timingsession_id=snum).values_list('tag_id',
            flat=True).distinct()

    for tag_id in tag_ids:

        # Get the name of the tag's owner.
        user = Tag.objects.get(id=tag_id).user
        if user:
            name = user.get_full_name()
        else:
            name = str(tag_id)

        # Calculate the splits for this tag in the current workout.
        interval = []
        times = TagTime.objects.filter(timingsession_id=snum, 
                                       tag_id=tag_id).order_by('time')
        for i in range(len(splits)-1):
            dt = times[i+1].time-times[i].time
            interval.append(dt.total_seconds())
        counter = range(1,len(interval)+1)    

        # Add the runner's data to the workout. 
        sdata['runners'].append({'name': name, 'counter': counter,
                                 'interval': interval})

    return sdata    

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

def parse_formatted_msg(string):
    """Extracts time data from a formatted reader message."""
    pass
