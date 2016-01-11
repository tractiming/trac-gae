"""
Utilities for interacting with Google Cloud Storage.

Examples
--------
>>> data = {'foo': 42, 'bar': 'spam'}
>>> json_write('trac-us.appspot.com', 'test/mydata.json', data)
>>> json_read('trac-us.appspot.com', 'test/mydata.json')
{'foo': 42, 'bar': 'spam'}
"""
import json
import os

import httplib2
from gcloud import storage
from oauth2client.client import SignedJwtAssertionCredentials

_IS_APPENGINE = os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine')

if _IS_APPENGINE:
    from oauth2client.appengine import AppAssertionCredentials

_PROJECT = 'trac-us'
_LOCATION = os.path.realpath(os.path.join(os.getcwd(),
                             os.path.dirname(__file__)))
_SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write'
]


def _get_http_auth():
    """Get an authorized `httplib2.Http` object.

    Detect if we are running on appengine or locally and authorize
    accordingly. (If locally, a json file with service account credentials is
    searched for in the project root directory.) The service has read/write
    access.
    """
    if _IS_APPENGINE:
        credentials = AppAssertionCredentials(scope=_SCOPES)
    else:
        # Look for credentials in a file named "gcs_credentials.json"
        # in the project's root directory.
        cred_dir = os.path.abspath(os.path.join(*(_LOCATION,
            os.path.pardir, os.path.pardir, os.path.pardir)))
        with open(os.path.join(cred_dir, 'gcs_credentials.json')) as _infile:
            creds = json.load(_infile)
        credentials = SignedJwtAssertionCredentials(creds['client_email'],
                                                    creds['private_key'],
                                                    scope=_SCOPES)
    return credentials.authorize(httplib2.Http())


def json_read(bucket, path):
    """Read a JSON file from cloud storage.
    
    Parameters
    ----------
    bucket : str
        Name of GCS bucket in which to store blob.
    path : str
        Full path to blob within `bucket`.
    """
    client = storage.Client(project=_PROJECT, http=_get_http_auth())
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(path)
    return json.loads(blob.download_as_string())


def json_write(bucket, path, data):
    """Write a JSON object to cloud storage.
    
    Parameters
    ----------
    bucket : str
        Name of GCS bucket in which to store blob.
    path : str
        Full path to blob within `bucket`.
    data : dict
        Data to be rendered to JSON and then uploaded.
    """
    client = storage.Client(project=_PROJECT, http=_get_http_auth())
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(path)
    return blob.upload_from_string(json.dumps(data))
