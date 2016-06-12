import requests
from bs4 import BeautifulSoup
from datetime import datetime

from .base import Scraper
from .exceptions import NoSuchAthlete, TooManyAthletes

PO10_BASE = 'http://www.thepowerof10.info/'
PO10_SEARCH_URL = PO10_BASE + 'athletes/athleteslookup.aspx'

YEAR_ROW = 1
TITLES_ROW = 2
PERF_ROW = 3


def perf_row_type(tr_elem):
    ''' tests what row type a tr elem from perf table is '''
    link = tr_elem.find_all('td')[0].a
    if link is not None:
        return YEAR_ROW
    if tr_elem.find_all('td')[0].text == 'Event':
        return TITLES_ROW
    return PERF_ROW


def get_name_from_profile(content):
    ''' given an html page returns the athlete name '''
    profile_soup = BeautifulSoup(content, 'html.parser')
    name_elem = profile_soup.find_all(class_="athleteprofilesubheader")[0].h2
    return name_elem.string.strip().encode('utf-8')


def get_club_from_profile(content):
    profile_soup = BeautifulSoup(content, 'html.parser')
    details = profile_soup.find_all(id='cphBody_pnlAthleteDetails')[0]
    return details.find_all('table')[1].find_all('table')[0].find_all('td')[1].text


def get_perf_table_from_profile(content):
    ''' given an html profile page returns the bs4 performance table '''
    soup = BeautifulSoup(content, 'html.parser')
    main_perfs_table = soup.find(id='cphBody_pnlPerformances')
    perfs_table = main_perfs_table.find_all('table')[1]
    return perfs_table


def get_results_from_row(row):
    cells = row.find_all('td')
    return {'event': cells[0].text,
            'position': cells[5].text,
            'meet': cells[10].text,
            'meet_id': cells[9].a.get('href').split('meetingid=')[1].split('&')[0],
            'date': datetime.strptime(cells[11].text, '%d %b %y'),
            'perf': cells[1].text}


class Po10Scraper(Scraper):
    '''
    Scrapes the Power of 10 websites (UK athletes)
    '''
    def get_athlete_details_from_url(self, url):
        ''' gets the athlete name from power of 10 '''
        r = requests.get(url)
        if r.status_code != 200:
            raise NoSuchAthlete("Unable to find athlete.")

        try:
            name = get_name_from_profile(r.content)
        except IndexError:
            # No name = no athlete
            raise NoSuchAthlete("Unable to find athlete.")

        return {'name': name, 'url': url}

    def get_athlete_results_from_url(self, url, limit=None):
        ''' returns performances from the athlete's power of 10 page. '''
        # Use viewby=date parameter to order results by date
        r = requests.get(url, params={'viewby': 'date'})

        # Here there is no validation that id is valid. We assume id is legit
        perfs_table = get_perf_table_from_profile(r.content)

        perfs = []
        for row in perfs_table.find_all('tr'):
            if perf_row_type(row) != PERF_ROW:
                continue
            cells = row.find_all('td')
            perfs.append(get_results_from_row(row))

            if limit == len(perfs):
                break
        return perfs

    def search(self, firstname='', surname='', club=''):
        r = requests.get(PO10_SEARCH_URL, params={'firstname': firstname,
                                                  'surname': surname,
                                                  'club': club})
        if r.history:
            # We have been redirected to an athlete profile page
            name = get_name_from_profile(r.content)
            url = r.url
            club = get_club_from_profile(r.content)
            return [{'name': name, 'club': club, 'url': url}]

        results = []
        soup = BeautifulSoup(r.content, 'html.parser')

        # Check errors - we may have either too many athletes found or
        # not a detailed enough search (fewer than 3 letters)
        request_error = soup.find_all(id='cphBody_lblRequestErrorMessage')
        results_error = soup.find_all(id='cphBody_lblResultsErrorMessage')
        if request_error and 'Please enter at least 3 characters' in request_error[0].text:
            raise ValueError('Search terms not detailed enough.')
        elif results_error and 'Too many athletes found.' in results_error[0].text:
            raise TooManyAthletes('Found too many athletes for search.')

        search_results = soup.find(id='cphBody_pnlResults')
        rows = search_results.find_all('tr')

        for row in rows[1:-1]:  # First row is header, last is ignored
            cells = row.find_all('td')
            name = cells[0].text + ' ' + cells[1].text
            club = cells[7].text
            url = PO10_BASE + 'athletes/' + cells[8].a.get('href')
            results.append({'name': name, 'club': club, 'url': url})
        return results
