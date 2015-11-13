from django.core.cache import cache
from django.utils import timezone
from trac.models import TimingSession, Split, Tag, Reader, Athlete

def create_phone_split(athlete_id, time):
    """
    Create a new split based on an incoming time. This is a separate
    function since each post from a reader may contain multiple splits.
    This is not an actual endpoint.
    """
    print 'Create split debug:', athlete_id, time
    


    try:
        athlete = Athlete.objects.get(id=athlete_id)
    except:
        return -1

    #reader = athlete.team.coach.reader_set.all()[0]
    reader = None
    
    # Create new TagTime.
    if time is not None:
        dtime = timezone.datetime.strptime(time, "%Y/%m/%d %H:%M:%S.%f") 
        timestamp = int((dtime-timezone.datetime(1970, 1, 1)).total_seconds()*1000)
    else:
        timestamp = None
        
    new_split = Split(tag=athlete.tag, athlete=athlete, reader=reader,
                      time=timestamp) 
    
    try:
        new_split.save()
    except:
        return -1

    # Add the split to all sessions active and having a related reader.
    for session in [sessions for sessions in TimingSession.objects.all() if sessions.active]:
        # If the session has a set of registered tags, and the current tag is
        # not in that set, ignore the split.
        if ((not session.use_registered_tags_only) or (tag in
                session.registered_tags.all())):
            session.splits.add(new_split.pk)

        # Destroying the cache for this session will force the results to be
        # recalculated.
        session.clear_cache(athlete.id)
    
    return 0
