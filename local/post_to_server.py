import urllib2
import json
import argparse

endpoint = "http://www.trac-us.appspot.com/api/raceregistration"

def post_roster(roster_file):
    """
    Post a json roster of athletes and tags to the race registration endpoint.
    """
    with open(roster_file) as data_file:
        data = json.load(data_file)

    req = urllib2.Request(endpoint)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, data)
    return response


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--roster', default='')
    args = parser.parse_args()

    print post_roster(vars(args)['roster'])







