import urllib
import urllib2
from bs4 import BeautifulSoup
import csv

#site_open = urllib2.urlopen("https://www.tfrrs.org/athletes/4513882/Loyola_IL/Jamison_Dale.html")
def obtain_html(url):
	""" 
	PASS IN URL FROM OBTAIN_ID AND USE IT TO QUERY ATHLETE SPECIFIC DATA.
	"""
	request = urllib2.Request(url, headers={'User-Agent' : "PC"})
	site_open = urllib2.urlopen(request)	
	html = site_open.read()
	soup = BeautifulSoup(html, 'html.parser')
	all_tables = soup.find('div', attrs={'class' : 'meetresults'})
	#print all_tables
	table = all_tables.find('table', attrs={'id' : 'results_data'})
	#t_body = table.find('tbody')
	rows = table.find_all('tr')
	result = []
	for row in rows:
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		result.append(cols)
	
	return result
	"""
	with open("output.csv", "wb") as f:
		writer = csv.writer(f)
		for row in rows:
			cols = row.find_all('td')
			cols = [ele.text.strip() for ele in cols]
			print cols
			writer.writerow(cols)
	"""



def obtain_id (name, team, meet):
	"""
	THIS SECTION OBTAINS THE USER_ID FOR THE ATHLETE WE WANT IN THE TFFRS SYSTEM. 
	"""
	if name != "0 0":
		athlete_name = name
	else:
		athlete_name = "ATHLETE NAME"
	if team != 0:
		team_name = team
	else:
		team_name = "TEAM NAME"
	if meet != 0:
		meet_name = meet
	else:
		meet_name = "MEET NAME"
	url = "https://www.tfrrs.org/site_search.html"
	values = {"athlete" : athlete_name, "team" : team_name, "meet" : meet_name}
	data = urllib.urlencode(values)
	headers = {"User-Agent" : "PC"}
	request = urllib2.Request(url, data, headers)
	site_open = urllib2.urlopen(request)
	html = site_open.read()

	"""
	THIS SECTION PARSES OUR HTML TO OBTAIN THE ID NUMBER.
	"""
	soup = BeautifulSoup(html, 'html.parser')
	all_tables = soup.find('div', attrs={'class' : 'data'})
	#print all_tables
	table = all_tables.find('table')
	rows = table.find_all('tr')
	result = []
	#print athlete_name
	for row in rows:
		if athlete_name != "ATHLETE NAME":
			cols = row.find_all('td', attrs={'class': 'date'})
		else:
			cols = row.find_all('td', attrs={'class': 'date_submitted'})
		#print cols
		for ele in cols:
			#print ele
			ref = ele.text.strip()
			for a in ele.find_all('a', href=True):
				link = a['href']
			#print link
			if link:
				tmp = {'name': ref, 'link' : link}
				result.append(tmp)
	
	if result:
		return result
	else:
		return "DNE"
