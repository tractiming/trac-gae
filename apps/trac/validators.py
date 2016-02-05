import csv

from rest_framework.serializers import ValidationError

from trac.utils.file_util import xls_to_dictreader


_REQUIRED_COLS = ('first_name', 'last_name')


def roster_upload_validator(request, file_field='file',
                            required_fields=_REQUIRED_COLS):
    """Validate an uploaded roster.

    Check for valid file format (".csv", ".xls", or ".xlxs") and
    required columns.

    Returns
    -------
    roster : a csv.DictReader like object

    Raises
    ------
    ValidationError
        For incorrect file types/contents.
    """
    file_obj = request.data.pop('file', None)
    if not file_obj:
        raise ValidationError(['No file uploaded'])
    file_obj = file_obj[0]

    if file_obj.name.endswith('.csv'):
        roster = csv.DictReader(file_obj)
        fieldnames = roster.fieldnames
    elif (file_obj.name.endswith('.xls') or
          file_obj.name.endswith('.xlsx')):
        roster = xls_to_dictreader(file_obj.read())
        fieldnames = roster[0].keys() if roster else []
    else:
        raise ValidationError(['File format not recognized. Please '
                               'upload in .csv or .xls(x) format.'])

    if not all(field in fieldnames for field in required_fields):
        raise ValidationError(['File does not contain columns "{}" in '
                               'header'.format('", "'.join(required_fields))])

    return roster
