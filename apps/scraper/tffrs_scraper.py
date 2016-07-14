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
	if name != 0:
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

	#print html

	"""
	THIS SECTION PARSES OUR HTML TO OBTAIN THE ID NUMBER.
	"""
	flag = 0
	id_list = []
	current_id = []
	for letter in html:
		if flag == 0:	
			if letter == "<":
				#print "a"
				flag = 1
				index = 0
		elif flag == 1:
			string = 'A HREF="//www.tfrrs.org/athletes/'
			string2 = 'a href="//www.tfrrs.org/athletes/'
			if letter == string[index] and index == len(string)-1:
				flag = 2
			elif letter == string2[index] and index == len(string)-1:
				flag = 2
			elif letter == string[index] or letter == string2[index]:
				flag = 1
				index += 1
				#print index
			else:
				flag = 0
		elif flag == 2:
			if letter != '.':
				current_id.append(letter)
			else:
				id_list.append(current_id)
				current_id = []
				flag = 0
		else:
			flag = 0

	"""
	THIS SECTION WILL PARSE URL TO PASS INTO PARSER
	"""
	url_list = []
	for id_val in id_list:
		url = "https://www.tfrrs.org/athletes/"
		for val in id_val:
			url = url + val
		url = url + ".html"
		url_list.append(url)
	if url_list:
		return url_list
	else:
		return "DNE"