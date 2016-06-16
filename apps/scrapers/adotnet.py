from .base import Scraper
from .exceptions import NoSuchAthlete

import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

ADOTNET_BASE = 'http://www.athletic.net/'
ADOTNET_SEARCH_URL = 'http://www.athletic.net/Search.aspx/runSearch'


class AdotNetScraper(Scraper):
    '''
    TODO: Think about cross v track results (separate urls).
          Order race results?
    '''

    def get_athlete_details_from_url(self, url):
        r = requests.get(url)
        if r.status_code != 200:
            raise NoSuchAthlete("Unable to find athlete.")

        soup = BeautifulSoup(r.content, 'html.parser')

        try:
            name = soup.find('title').text.strip().split('-')[0].strip().encode('utf-8')
        except IndexError:
            # No name = no athlete
            raise NoSuchAthlete("Unable to find athlete.")

        return {'name': name, 'url': url}

    def get_athlete_results_from_url(self, url, limit=None):
        ''' returns performances from the athlete's athletic.net page. '''
        r = requests.get(url)

        soup = BeautifulSoup(r.content, 'html.parser')
        # Here there is no validation that id is valid. We assume it is
        possibles = soup.find(class_='athleteResults').find_all(class_='panel')

        perfs = []
        for season in possibles:
            year = list(season.children)[0].text.split(' ')[0]
            results = list(season.children)[1].find(class_='panel-body')

            for child in results.children:
                if child.name == 'h5':
                    event = child.text
                else:
                    # we have a table of results for the current event
                    for result in child.find_all('tr'):
                        cells = result.find_all('td')
                        try:
                            perfs.append({'event': event,
                                          'position': cells[0].text.strip(),
                                          'meet': cells[3].text,
                                          'meet_id': cells[3].a.get('href').split('Meet=')[1].split('#')[0],
                                          'date': datetime.strptime(cells[2].text + ' ' + year, '%b %d %Y'),
                                          'perf': cells[1].text})
                        except Exception as e:
                            print e, cells
                            continue

        return perfs[0:limit]

    def search(self, firstname='', surname='', team=''):
        ret = []
        query = ' '.join([firstname, surname, team])
        data = json.dumps({'q': query, 'fq': "t:a", 'start': 0})
        headers = {'Content-Type': 'application/json'}
        r = requests.post(ADOTNET_SEARCH_URL, data=data, headers=headers)

        resp_html = r.json()['d']['results']
        soup = BeautifulSoup(resp_html, 'html.parser')
        results = soup.find_all(class_='Athlete')
        for r in results:
            name = r.find(class_='Title').text.strip()
            links = r.find_all('a')
            url = None
            team = set()
            for link in links:
                try:
                    if link.get('class')[0] == 'TFLink':
                        url = ADOTNET_BASE + link.get('href')
                except TypeError:
                    pass
                if 'School' in link.get('href'):
                    team.add(link.text.strip())
            ret.append({'name': str(name), 'team': str('/'.join(list(team))), 'url': str(url)})

        return ret
