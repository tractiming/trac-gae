"""
Utilities for interacting with Google Cloud Storage.

Examples
--------
>>> data = {'foo': 42, 'bar': 'spam'}
>>> json_write('trac-us.appspot.com', 'test/mydata.json', data)
>>> json_read('trac-us.appspot.com', 'test/mydata.json')
{'foo': 42, 'bar': 'spam'}
"""
import contextlib
import json
import os
import tempfile

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
    'https://www.googleapis.com/auth/devstorage.full_control'
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


def _get_blob(bucket, path):
    """Get an existing blob from GCS."""
    client = storage.Client(project=_PROJECT, http=_get_http_auth())
    bucket = client.get_bucket(bucket)
    return bucket.get_blob(path)


def _make_blob(bucket, path):
    """Create a new blob in GCS."""
    client = storage.Client(project=_PROJECT, http=_get_http_auth())
    bucket = client.get_bucket(bucket)
    return bucket.blob(path)


def json_read(bucket, path):
    """Read a JSON file from cloud storage.

    Parameters
    ----------
    bucket : str
        Name of GCS bucket in which to store blob.
    path : str
        Full path to blob within `bucket`.
    """
    blob = _get_blob(bucket, path)
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
    blob = _make_blob(bucket, path)
    return blob.upload_from_string(json.dumps(data))


@contextlib.contextmanager
def gcs_writer(bucket, path, make_public=False):
    """A context for writing files to cloud storage.

    Parameters
    ----------
    bucket : str
        Save the file in this bucket.
    path : str
        Save the file contents to this location when exiting the
        context.
    make_public : bool, optional
        If True, make the file contents public.

    Yields
    ------
    file object

    Examples
    --------
    >>> data = [['foo', '1'], ['bar', '2']]
    >>> with gcs_writer('bucket', 'path/to.csv') as _file:
    ...     writer = csv.writer(_file)
    ...     for d in data:
    ...         writer.writerow(d)
    """
    temp = tempfile.TemporaryFile()
    try:
        yield temp
        temp.seek(0, os.SEEK_END)
        size = temp.tell()

        blob = _make_blob(bucket, path)
        blob.upload_from_file(temp, rewind=True, size=size)

        if make_public:
            blob.make_public()
    finally:
        temp.close()


def get_public_link(bucket, path):
    """Retrieve a public link to a file in GCS."""
    return _get_blob(bucket, path).public_url
