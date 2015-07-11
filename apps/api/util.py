from django.core.cache import cache
from django.utils import timezone
from trac.models import TimingSession, TagTime, Tag, Reader

def create_split(reader_id, tag_id, time):
    """
    Create a new tagtime based on an incoming split. This is a separate
    function since each post from a reader may contain multiple tagtimes.
    This is not an actual endpoint.
    """
    print 'Create split debug:', reader_id, tag_id, time
    
    # Get the tag and reader associated with the notification. Note that if the
    # tag or reader has not been established in the system, the split will be
    # ignored here.
    try:
        reader = Reader.objects.get(id_str=reader_id)
        tag = Tag.objects.get(id_str=tag_id)
    except:
        return -1
   
    # Create new TagTime.
    dtime = timezone.datetime.strptime(time, "%Y/%m/%d %H:%M:%S.%f") 
    #TODO: why does the next line not work?
    #dtime = timezone.pytz.utc.localize(dtime)
    ms = int(str(dtime.microsecond)[:3])
    tt = TagTime(tag_id=tag.id, time=dtime, reader_id=reader.id, milliseconds=ms)
    try:
        tt.save()
    except:
        return -1

    # Add the TagTime to all sessions active and having a related reader.
    for s in reader.active_sessions:
        # If the session has a set of registered tags, and the current tag is
        # not in that set, ignore the split.
        reg_tags = s.registered_tags.all()
        if (not reg_tags) or (tt.tag in reg_tags):
            s.tagtimes.add(tt.pk)

        # Destroying the cache for this session will force the results to be
        # recalculated.
        cache.delete(('ts_%i_results' %s.id))
        cache.delete(('ts_%i_athlete_names' %s.id))
    
    return 0
