import json
from firebase import firebase

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, pagination, filters
import trac.models

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
		f = firebase.FirebaseApplication('https://dazzling-torch-965.firebaseio.com/', None)
		r = f.put('/sessions', str(session_id), individual_results_json, {'print': 'pretty'})
		return Response(status=status.HTTP_202_ACCEPTED)
	except ObjectDoesNotExist:
		return Response(status=status.HTTP_404_BAD_REQUEST)