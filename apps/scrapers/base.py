class Scraper(object):
    '''
    Base class for a Scraper object. These are used to access running result
    websites and scrape data (athlete information and race results).

    Contains the following methods which should be implemented when subclassing:
     - get_athlete_results_from_url
     - get athlete_details_from_url
     - search
    '''
    def __init__(self):
        pass

    def get_athlete_results_from_url(self, url, limit=None):
        raise NotImplementedError()

    def get_athlete_details_from_url(self, url):
        raise NotImplementedError()

    def search(self, **kwargs):
        raise NotImplementedError()
