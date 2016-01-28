"""
A backend for using Google Cloud Storage within Django.
See: https://docs.djangoproject.com/en/1.8/howto/custom-file-storage/
"""
import contextlib
import os
import tempfile

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from gcloud import storage

from backends import _gcs


@deconstructible
class GCSStorage(Storage):
    """Storage backend for GCS.

    Parameters
    ----------
    bucket : str, optional
        Root bucket in which to store objects. Defaults to the
        `GCS_DEFAULT_BUCKET` defined in the settings file.
    """
    def __init__(self, bucket=None):
        if bucket is None:
            bucket = settings.GCS_DEFAULT_BUCKET
        self._bucket = bucket

    def _open(self, name, mode='rb'):
        temp = tempfile.TemporaryFile()
        blob = _gcs._get_blob(self._bucket, name)
        blob.download_to_file(temp)
        temp.seek(0)
        return temp

    def _save(self, name, content):
        content.seek(0, os.SEEK_END)
        size = content.tell()
        blob = _gcs._make_blob(self._bucket, name)
        blob.upload_from_file(content, rewind=True, size=size)
        return blob.name

    def delete(self, name):
        blob = _gcs._get_blob(self._bucket, name)
        if blob is not None:
            return blob.delete()

    def exists(self, name):
        return _gcs._make_blob(self._bucket, name).exists()

    def listdir(self, path):
        client = storage.Client(project=_gcs._PROJECT,
                                http=_gcs._get_http_auth())
        bucket = client.get_bucket(self._bucket)

        dirs = set()
        files = set()
        blobs = map(lambda x: x.name.lstrip(path).lstrip('/'),
                    bucket.list_blobs(prefix=path))
        for blob in blobs:
            fnames = blob.rsplit('/')
            if len(fnames) == 1:
                files.add(fnames[0])
            else:
                dirs.add(fnames[0].split('/', 1)[0])

        return list(dirs), list(files)

    def size(self, name):
        blob = _gcs._get_blob(self._bucket, name)
        if blob is not None:
            return blob.size

    def url(self, name):
        blob = _gcs.get_blob(self._bucket, name)
        if blob is not None:
            return blob.public_url
