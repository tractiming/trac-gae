from rest_framework.response import Response

import stats.stats_calcs as stats
from stats.serializers import PerformanceRecord_Serializer
from stats.models import PerformanceRecord
from stats.filters import PerformanceRecord_Filter
from trac.models import TimingSession, Coach
from trac.utils.user_util import is_athlete, is_coach

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mass_mail
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from rest_framework import viewsets, permissions, status, pagination, filters
from rest_framework.decorators import api_view, permission_classes, detail_route
from rest_framework.parsers import FileUploadParser


DEFAULT_DISTANCES = [100, 200, 400, 800, 1000, 1500,
1609, 2000, 3000, 5000, 10000]
DEFAULT_TIMES = [14.3, 27.4, 61.7, 144.2, 165, 257.5,
278.7, 356.3, 550.8, 946.7, 1971.9, ]


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def analyze(request):
	"""
	Returns auto_edit splits.
	---
	parameters:
	- name: id
	description: Session ID
	paramType: form
	required: true
	type: int
	"""
	idx = request.POST.get('id')
	session = TimingSession.objects.get(pk=idx)
	results = session.individual_results()
	print(results)
	data = [{
	'name': result.user_id,
	'times': result.splits,
	}for result in results]
	analyzed_times = stats.investigate(data)

	return Response(analyzed_times)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def VO2Max(request):
	"""
	TODO: Fix
	"""
	user = request.user
	if is_coach(user):
		print user
		result = []
		cp = Coach.objects.get(user = user)
		t = cp.team_set.all()
		for team in t:
			for athlete in team.athlete_set.all():
				sum_VO2 = 0
				count = 0
				for entry in athlete.performancerecord_set.all():
					print entry
					sum_VO2 += entry.VO2
					count += 1
					try:
						avg_VO2 = sum_VO2 / count
						avg_VO2 = avg_VO2 / .9
						#avg_VO2 = int(avg_VO2)
						vVO2 = 2.8859 + .0686 * (avg_VO2 - 29)
						vVO2 = vVO2 / .9
					except:
						avg_VO2 = 'None'
						vVO2 = 1
				print 'VO2: ' + str(avg_VO2)
				print 'vVO2: ' + str(vVO2)
				#print '100m: ' + str(100/vVO2)
				#print '200m: ' + str(200/vVO2)
				#print '400m: ' + str(400/vVO2)
				#print '800m: ' + str(800/vVO2)
				#print '1000m: ' + str(1000/vVO2)
				#print '1500m: ' + str(1500/vVO2)
				#print '1600m: ' + str(1609/vVO2)
				#print '3000m: ' + str(3000/vVO2)
				#print '5000m: ' + str(5000/vVO2)
				#print '10000m: ' + str(10000/vVO2)
	elif is_athlete(user):
		ap = Athlete.objects.get(user = user)

	else:
		print "need oauth token"

	return Response(avg_VO2)

class PerformanceRecordViewSet(viewsets.ModelViewSet):

	serializer_class = PerformanceRecord_Serializer
	permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
	pagination_class = pagination.LimitOffsetPagination
	filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
	filter_class = PerformanceRecord_Filter
	search_fields = ('event_name', 'athlete_first_name', 'athlete_last_name', 'team_name', 'distance')

	def get_queryset(self):
		"""Filter sessions by user.

		If the user is an athlete, list the sessions he has
		completed. If the user is a coach, list the sessions he owns.
		Otherwise, list all public sessions.
		"""
		user = self.request.user

		if is_athlete(user):
			atl = Athlete.objects.get(user = user)
			return atl.performancerecord_set.all()
		elif is_coach(user):
			cp = Coach.objects.get(user = user)
			return PerformanceRecord.objects.filter(athlete__team__coach = cp)

"""
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def est_distance(request):
"""
"""
TODO: Fix
Updates user individual time tables using distance prediction.
"""
"""
#SETUP and parse dataList
user = request.user
idx = request.POST.get('id')
ts = TimingSession.objects.get(id=idx)
run = ts.individual_results()
dataList = []
for r in run:
times = r[3]
for index, item in enumerate(times):
times[index] = float(item)
name = r[0]
dataList.append({'name': name, 'times': times})

#Analysis split_times is distance prediction, r_times is individual runner times, and r_dicts is auto_edit dictionary
split_times, r_times = stats.calculate_distance(dataList)

#Interpolate split_times to data in coach's table.
#Predict the distance run.
cp = Coach.objects.get(user=user)
r = cp.performancerecord_set.all()
distanceList = []
for interval in split_times.keys():
int_time = split_times[interval]
time_delta = 1000000
for row in r:
if abs(int_time-row.time) < time_delta:
time_delta = abs(int_time-row.time)
selected = row.distance

#validate distance predictions with coach and update coach table as necessary.
var = raw_input("Did you run a "+str(selected)+" in "+str(interval-1)+" splits?")
if var == 'no':
var2 = raw_input("What was the distance? ")
if var2 == 'none':
continue
else:
length = int(var2)
s = cp.performancerecord_set.get(distance = length)
s.time = (s.time + int_time)/2
s.save()
distanceList.append({'Splits': interval-1, 'Distance': length})
else:
distanceList.append({'Splits': interval-1, 'Distance': selected})

#update each individual runner tables with their own data for distances predicted above.
for runner in r_times:
return_dict = []
accumulate_VO2 = 0
count_VO2 = 0
accumulate_t_VO2 = 0
count_t_VO2 = 0
username = runner['name']
a_user = User.objects.get(id = username)
ap = Athlete.objects.get(user = a_user)
cp.athletes.add(ap)
for results in runner['results']:
splits = results['splits']
times = results['times']
for distance in distanceList:
if splits == distance['Splits'] and times != 0:
try:
r= ap.performancerecord_set.get(distance= distance['Distance'], interval= results['interval'])
r.time = (r.time + times)/2
velocity = r.distance / (r.time/60)
t_velocity = r.distance/ (times/60)
t_VO2 = (-4.60 + .182258 * t_velocity + 0.000104 * pow(t_velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * times/60)) + .2989558 * pow(2.78, (-.1932605 * times/60)))
VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * r.time/60)) + .2989558 * pow(2.78, (-.1932605 * r.time/60)))
VO2 = int(VO2)
t_VO2 = int(t_VO2)
r.VO2 = VO2
r.save()
except:
velocity = distance['Distance']/ (times/60)
VO2 = (-4.60 + .182258 * velocity + 0.000104 * pow(velocity, 2)) / (.8 + .1894393 * pow(2.78, (-.012778 * times/60)) + .2989558 * pow(2.78, (-.1932605 * times/60)))
VO2 = int(VO2)
t_VO2 = VO2
r = PerformanceRecord.objects.create(distance=distance['Distance'], time=times, interval= results['interval'], VO2= VO2)
accumulate_t_VO2 += t_VO2
count_t_VO2 += 1
accumulate_VO2 += VO2
count_VO2 += 1
ap.performancerecord_set.add(r)
temp_t_VO2 = accumulate_t_VO2 / count_t_VO2
temp_VO2 = accumulate_VO2 / count_VO2
return_dict.append({"runner":runner, "CurrentWorkout":temp_t_VO2, "Average":temp_VO2})

#LOG: print return_dict
return Response({}, status.HTTP_200_OK)
"""
