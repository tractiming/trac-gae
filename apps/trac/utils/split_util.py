import datetime

from django.core.cache import cache
from django.utils import timezone
from trac.models import TimingSession, Split, Tag, Reader


_EPOCH = datetime.datetime.utcfromtimestamp(0)


def create_split(reader_str, tag_str, time):
    """
    Create a new split based on an incoming time. This is a separate
    function since each post from a reader may contain multiple splits.
    This is not an actual endpoint.
    """
    print 'Create split debug:', reader_str, tag_str, time
    
    # Get the tag and reader associated with the notification. Note that if the
    # tag or reader has not been established in the system, the split will be
    # ignored here.
    try:
        reader = Reader.objects.get(id_str=reader_str)
        tag = Tag.objects.get(id_str=tag_str)
    except:
        return -1
   
    # Create new TagTime.
    dtime = timezone.datetime.strptime(time, "%Y/%m/%d %H:%M:%S.%f") 
    timestamp = int((dtime-timezone.datetime(1970, 1, 1)).total_seconds()*1000)
    new_split = Split(tag=tag, athlete=tag.athlete, reader=reader,
                      time=timestamp) 
    
    try:
        new_split.save()
    except:
        return -1

    # Add the split to all sessions active and having a related reader.
    for session in reader.active_sessions:
        # If the session has a set of registered tags, and the current tag is
        # not in that set, ignore the split.
        if ((not session.use_registered_tags_only) or (athlete in
                session.registered_tags.all())):
            session.splits.add(new_split.pk)

        # Destroying the cache for this session will force the results to be
        # recalculated.
        session.clear_cache(tag.athlete.id)
    
    return 0

def convert_time(raw_time):
    """Detect the format of the time (int, timestamp, datetime, etc.)
    and convert to the big integer format used internally.
    """
    if isinstance(raw_time, int):
        return raw_time
    if isinstance(raw_time, datetime.datetime):
        pass
    else:
        try:
            # Integer formatted in a string.
            int_time = int(raw_time)
            return int_time
        except ValueError:
            pass




