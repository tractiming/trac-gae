from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.core.cache import cache
from django.db import IntegrityError
import json
from common.models import TimingSession, TagTime, Tag, Reader
from util import parse_msg, get_splits

_USE_CACHING = False

class JSONResponse(HttpResponse):
    """Http response that renders its content to JSON."""
    def __init__(self, data, **kwargs):
        content = json.dumps(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

@csrf_exempt
def workout_data(request):
    """Interfaces with readers/clients to provide up-to-date workout info."""

    # A get request returns the JSON string with current workout information.
    # To get the info, we first try to read from the cache, if it is not there,
    # recalculate the splits and save to cache.
    if request.method == 'GET':
        #return HttpResponse(200)
        w_num = request.GET['w']

        if _USE_CACHING:
            cache_name = 'w'+str(w_num)+'_cached'
            split_data = cache.get(cache_name)
            if not split_data:
                split_data = get_splits(w_num)
                cache.set(cache_name, split_data)
        else:
            split_data = get_splits(w_num)

        return JSONResponse(split_data)
    
    # A post request adds the split to the database with the correct tag, time,
    # and workout information.
    elif request.method == 'POST':
        
        print request.POST
        #print request.META
        return HttpResponse()
        """
        # Get the raw data from the post.
        data = parse_msg(request.POST['m'])
        
        # Get the workouts to which the tag currently belongs.
        t = Tag.objects.get(id_str=data['name'])
        r = Reader.objects.get(num=int(request.POST['r']))
        active_workouts = r.active_workouts()
        
        # Create new splits.
        for w in active_workouts:
            
            # Save the new split in the db.
            try:
                s = Split(tag=t, time=data['time'], reader_id=r.id, workout_id=w.id)
                s.save()
            except IntegrityError:
                pass

            # Clear the workout cache.
            cache.delete('w'+str(w.num)+'_cached')
        """
        return HttpResponse(200)
