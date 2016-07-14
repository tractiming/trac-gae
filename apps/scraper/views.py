from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from stats.models import PerformanceRecord
from trac.models import *

import tffrs_scraper as tffrs_scraper
import adotnet as adotnet_scraper
import po10 as po10_scraper

import datetime
import time

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def TFFRS_query(request):
	First_Name = request.POST.get('first')
	Last_Name = request.POST.get('last')
	Team = request.POST.get('team')
	Full_Name = First_Name + " " + Last_Name
	search_results = tffrs_scraper.obtain_id(Full_Name, Team, 0)

	return Response(search_results)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def TFFRS_fetch(request):
	url = request.POST.get('url')
	First_Name = request.POST.get('first')
	Last_Name = request.POST.get('last')

	"""Now we have a list of lists of times so we will now store in DB"""
	result = tffrs_scraper.obtain_html(url)
	for row in result:
		date = row[0]

		edited_date = date[0:5]
		edited_date_2 = date[-2:]
		edited_date = edited_date.replace("/", "-")
		edited_date_2 = "20" + edited_date_2
		perf_date = edited_date_2 + "-" + edited_date

		meet = row[1]
		if row[3] == "Mile":
			distance = 1609
		else:	
			distance = int(row[3].replace(",",""))
		time = row[5]
		time_2 = time.split(':')
		minutes = float(time_2[0])
		seconds = float(time_2[1])
		perf_time = (60.0 * minutes) + seconds
		usr = User.objects.get(first_name= First_Name, last_name= Last_Name)
		atl = Athlete.objects.get(user = usr)
		PerformanceRecord.objects.get_or_create(date= perf_date, event_name= meet, distance= distance, time= perf_time, athlete=atl)

	return Response(result)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def AdotNet_query(request):
	First_Name = request.POST.get('first')
	Last_Name = request.POST.get('last')
	Team = request.POST.get('team')
	search_result = adotnet_scraper.AdotNetScraper().search(firstname=First_Name, surname=Last_Name, team=Team)

	return Response(search_result)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def AdotNet_fetch(request):
	url = request.POST.get('url')
	result = adotnet_scraper.AdotNetScraper().get_athlete_results_from_url(url)
	details = adotnet_scraper.AdotNetScraper().get_athlete_details_from_url(url)

	Full_Name = details['name']
	Names = Full_Name.split(' ')
	firstname = Names[0]
	surname = Names[1]
	usr = User.objects.get(first_name=firstname, last_name=surname)
	atl = Athlete.objects.get(user = usr)
	#FYI DJANGO QUERIES ARE CASE SENSITIVE

	for row in result:
		perf_date = row['date']
		meet = row['meet']

		distance = row['event']
		new_distance = distance
		if new_distance == "1 Mile":
			new_distance = 1609
		elif new_distance == "2 Miles":
			new_distance = (1609 * 2)
		else:
			try:
				new_distance = int(new_distance[:-6].replace(',', ''))
			except:
				new_distance = 0
				
		time = row['perf']
		if time == "DNF":
			perf_time = 0
		else:
			time_2 = time.split(':')
			try:
				seconds = float(time_2[1])
				minutes = float(time_2[0])
			except:
				seconds = float(time_2[0])
				minutes = 0.0
			perf_time = (60.0 * minutes) + seconds

		if new_distance != 0:
			PerformanceRecord.objects.get_or_create(date= perf_date, event_name= meet, distance= new_distance, time= perf_time, athlete=atl)
		else:
			continue
	return Response(result)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def Po10_query(request):
	First_Name = request.POST.get('first')
	Last_Name = request.POST.get('last')
	Team = request.POST.get('team')
	search_result = po10_scraper.Po10Scraper().search(firstname=First_Name, surname=Last_Name, team=Team)

	return Response(search_result)

@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def Po10_fetch(request):
	url = request.POST.get('url')
	result = po10_scraper.Po10Scraper().get_athlete_results_from_url(url)
	details = po10_scraper.Po10Scraper().get_athlete_details_from_url(url)#

	Full_Name = details['name']
	Names = Full_Name.split(' ')
	firstname = Names[0]
	surname = Names[1]
	usr = User.objects.get(first_name=firstname, last_name=surname)
	atl = Athlete.objects.get(user = usr)
	#FYI DJANGO QUERIES ARE CASE SENSITIVE

	for row in result:
		perf_date = row['date']
		meet = row['meet']

		distance = row['event']
		new_distance = distance
		try:
			new_distance = int(new_distance)
		except:
			if distance == "Mile":
				new_distance = 1609
			elif distance == "2Miles":
				new_distance = (2 * 1609)
			elif distance == "5K":
				new_distance = 5000
			elif distance == "8K":
				new_distance = 8000
			elif distance == "10K":
				new_distance = 10000
			else:
				new_distance = 0

		time = row['perf']
		if time == "DNF":
			perf_time = 0
		else:
			time_2 = time.split(':')
			try:
				seconds = float(time_2[1])
				minutes = float(time_2[0])
			except:
				seconds = float(time_2[0])
				minutes = 0.0
			perf_time = (60.0 * minutes) + seconds

		if new_distance != 0:
			PerformanceRecord.objects.get_or_create(date= perf_date, event_name= meet, distance= new_distance, time= perf_time, athlete=atl)
		else:
			continue

	return Response(result)