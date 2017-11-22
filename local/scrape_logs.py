"""
Scrape logs from AppEngine to find split messages posted by the readers but
not necessarily saved to the database. Save results to a CSV file with "time",
"tag", and "reader" columns.
"""
import argparse
import ast
import csv
import re
import subprocess
import tempfile


def parse_split_logs(filename, num_days=2):
    """Get a list of log messages from GAE and filter those that contain a
    debug split message. Save raw split information into new file named
    `filename`.
    """
    with tempfile.NamedTemporaryFile(mode='r+') as _temp:
        subprocess.call(['appcfg.py',
                         '-n', str(num_days),
                         '--include_all',
                         '--severity=0',
                         'request_logs',
                         '.',
                         _temp.name])
        _temp.seek(0)
        with open(filename, 'w') as _parsed:
            writer = csv.DictWriter(_parsed,
                                    fieldnames=['time', 'tag', 'reader'],
                                    extrasaction='ignore',
                                    quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for line in _temp:
                match = re.search("Creating split(?:.*)(\[\{.*\}\])", line)
                if match is None:
                    continue

                splits = ast.literal_eval(match.groups()[0])
                for split in splits:
                    writer.writerow(split)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename',
                        help='Save splits in this file (formatted as a CSV)')
    parser.add_argument('-n', '--num-days', type=int,
                        help='Number of days to go back when searching logs')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    parse_split_logs(args.filename, num_days=args.num_days)
