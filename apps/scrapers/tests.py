from django.test import TestCase

from .po10 import Po10Scraper
from .exceptions import TooManyAthletes, NoSuchAthlete


OVETT = 'http://www.thepowerof10.info/athletes/profile.aspx?athleteid=2424'
COE = 'http://www.thepowerof10.info/athletes/profile.aspx?athleteid=1987'
BAD = 'http://www.thepowerof10.info/athletes/profile.aspx?athleteid=nope'


class Po10TestCase(TestCase):
    '''
    Not all these tests call the power of 10 website to ensure the html
    has not changed. Do not need to be run in the regular test suite.
    '''
    def setUp(self):
        self.scraper = Po10Scraper()

    def test_search_for_ovett(self):
        results = self.scraper.search(firstname='steve', surname='ovett')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {'name': 'Steven Ovett', 'team': 'Annan', 'url': OVETT})

    def test_search_for_seb_coe_redirect(self):
        ''' this search redirects to seb coe's profile on po10 '''
        results = self.scraper.search(firstname='seb', surname='coe', team='Haringey')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {'name': 'Sebastian Coe', 'team': 'Haringey', 'url': COE})

    def test_no_athletes_found(self):
        results = self.scraper.search(firstname='Lebron', surname='James')
        self.assertEqual(len(results), 0)

    def test_too_many_athletes(self):
        ''' too many start with 'Ste' '''
        self.assertRaises(TooManyAthletes, self.scraper.search, firstname='ste')

    def test_bad_search(self):
        ''' only 1 letter (min 3) '''
        self.assertRaises(ValueError, self.scraper.search, firstname='s')

    def test_get_ovett_details(self):
        details = self.scraper.get_athlete_details_from_url(OVETT)
        self.assertEqual(details, {'url': OVETT, 'name': 'Steven Ovett'})

    def test_no_athlete(self):
        self.assertRaises(NoSuchAthlete, self.scraper.get_athlete_details_from_url, BAD)

    def test_get_ovett_results(self):
        results = self.scraper.get_athlete_results_from_url(OVETT)
        self.assertEqual(len(results), 135)
        self.assertEqual(results[0]['event'], '10K')

    def test_get_results_with_limit(self):
        results = self.scraper.get_athlete_results_from_url(OVETT, limit=10)
        self.assertEqual(len(results), 10)
