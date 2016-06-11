import requests
from bs4 import BeautifulSoup

from .base import Scraper
from .exceptions import NoSuchAthlete


class Po10Scraper(Scraper):
    '''
    Scrapers the Power of 10 websites (UK athletes)
    '''
    def get_athlete_details_from_url(self, url):
        ''' gets the athlete name from power of 10 '''
        r = requests.get(url)
        if r.status_code != 200:
            raise NoSuchAthlete("Unable to find athlete.")

        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            name = soup.find_all(class_="athleteprofilesubheader")[0].h2.string.strip().encode("utf-8")
        except IndexError:
            # No name = no athlete
            raise NoSuchAthlete("Unable to find athlete.")

        return {'name': name, 'url': url}
