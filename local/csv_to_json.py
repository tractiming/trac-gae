import csv
import json
import datetime
import argparse

def create_race_info(athlete_file, reader, race_name=None, race_date=None, d_name=None):
    """
    Converts race information into formatted json that can be posted to the server.
    """
    if race_name is None:
        race_name = athlete_file.split('.')[0]
    if race_date is None:
        race_date = str(datetime.date.today())
    if d_name is None:
        d_name = race_name + '-director'

    race_data = {'race_name': race_name, 'race_date': race_date, 'readers': [reader],
            'director_username': d_name, 'athletes': []}

    input_file = csv.DictReader(open(athlete_file))
    for row in input_file:
        race_data['athletes'].append(row)

    output_file = athlete_file.split('.')[0]+'.json'
    json.dump(race_data, open(output_file, 'w'), indent=4, sort_keys=False)
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reader', default='')
    parser.add_argument('-a', '--athlete_file', default='')
    parser.add_argument('-n', '--race-name', default=None)
    parser.add_argument('-d', '--race-date', default=None)
    parser.add_argument('-o', '--d_name', default=None)
    args = parser.parse_args()

    create_race_info(**vars(args))
