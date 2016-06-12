from .base import Scraper
from .exceptions import NoSuchAthlete

from datetime import datetime
import requests
from bs4 import BeautifulSoup


class AdotNetScraper(Scraper):

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
        ''' returns performances from the athlete's power of 10 page. '''
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

    def search(self, **kwargs):
        raise NotImplementedError()
