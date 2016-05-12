import json
import urlparse
import os

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, pagination, filters
import trac.models


class Firebase():
    ROOT_URL = '' #no trailing slash

    def __init__(self, root_url, auth_token=None):
        self.ROOT_URL = root_url.rstrip('/')
        self.auth_token = auth_token

    #These methods are intended to mimic Firebase API calls.

    def child(self, path):
        root_url = '%s/' % self.ROOT_URL
        url = urlparse.urljoin(root_url, path.lstrip('/'))
        return Firebase(url)

    def parent(self):
        url = os.path.dirname(self.ROOT_URL)
        #If url is the root of your Firebase, return None
        up = urlparse.urlparse(url)
        if up.path == '':
            return None #maybe throw exception here?
        return Firebase(url)

    def name(self):
        return os.path.basename(self.ROOT_URL)

    def toString(self):
        return self.__str__()
    def __str__(self):
        return self.ROOT_URL

    def set(self, value):
        return self.put(value)

    def push(self, data):
        return self.post(data)

    def update(self, data):
        return self.patch(data)

    def remove(self):
        return self.delete()

    
    #These mirror REST API functionality

    def put(self, data):
        return self.__request('put', data = data)

    def patch(self, data):
        return self.__request('patch', data = data)

    def get(self):
        return self.__request('get')

    #POST differs from PUT in that it is equivalent to doing a 'push()' in
    #Firebase where a new child location with unique name is generated and
    #returned
    def post(self, data):
        return self.__request('post', data = data)

    def delete(self):
        return self.__request('delete')


    #Private

    def __request(self, method, **kwargs):
        #Firebase API does not accept form-encoded PUT/POST data. It needs to
        #be JSON encoded.
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'])

        params = {}
        if self.auth_token:
            if 'params' in kwargs:
                params = kwargs['params']
                del kwargs['params']
            params.update({'auth': self.auth_token})

        r = requests.request(method, self.__url(), params=params, **kwargs)
        r.raise_for_status() #throw exception if error
        return r.json()


    def __url(self):
        #We append .json to end of ROOT_URL for REST API.
        return '%s.json' % self.ROOT_URL


def firebase_post(session_id):
	"""
	Firebase Test. 

	"""

	session = trac.models.TimingSession.objects.get(id=session_id)
	# Filter out IDs that do not belong to valid athletes.
	all_athletes = True

	raw_results = session.individual_results()

	extra_results = []
	distinct_ids = set(session.splits.values_list('athlete_id',
	                                              flat=True).distinct())
	if (len(raw_results) < 10000) and all_athletes:
	    # Want to append results set with results for runners who are
	    # registered, but do not yet have a time. These results are added
	    # to the end of the list, since they cannot be ordered.
	    if len(raw_results) == 0:
	        extra_offset = 0 - session.num_athletes
	    else:
	        extra_offset = 0
	    extra_limit = 1000 - len(raw_results)
	    additional_athletes = []
	    for athlete in session.registered_athletes.all(
	            )[extra_offset:extra_limit]:
	        has_split = (session.id in athlete.split_set.values_list(
	            "timingsession", flat=True).distinct())

	        # If the athlete already has at least one split, they will
	        # already show up in the results.
	        if not has_split:
	            extra_results.append(session._calc_athlete_splits(
	                athlete.id))

	        distinct_ids |= set(session.registered_athletes.values_list(
	            'id', flat=True).distinct())

	results = {
	    'num_results': len(distinct_ids),
	    'num_returned': len(raw_results)+len(extra_results),
	    'results': []
	}

	for result in (raw_results + extra_results):
	    individual_result = {
	        'name': result.name,
	        'id': result.user_id,
	        'splits': [[str(split)] for split in result.splits],
	        'total': str(result.total),
	        'has_split': result.first_seen is not None,
	        'first_seen': result.first_seen,
	        'gender': result.gender,
	        'age': result.age,
	        'bib': result.bib
	    }
	    
	    results['results'].append(individual_result)


	try:
		individual_results_json = results
		fire_url = 'https://dazzling-torch-965.firebaseio.com/sessions/' + str(session_id) 
		f = Firebase(fire_url)
		print(f)
		r = f.put(individual_results_json)
		print(r)
		return Response(status=status.HTTP_202_ACCEPTED)
	except ObjectDoesNotExist:
		return Response(status=status.HTTP_404_BAD_REQUEST)