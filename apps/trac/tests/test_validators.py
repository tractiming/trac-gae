import tempfile

import xlrd
import xlwt
from django.test import TestCase
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory

from trac.validators import roster_upload_validator


class ValidatorTest(TestCase):

    def test_roster_upload_xls(self):
        """Test a roster uploaded in .xls format."""
        with tempfile.NamedTemporaryFile(suffix='.xls', mode='r+w') as _data:
            book = xlwt.Workbook()
            sheet = book.add_sheet('Roster')
            rows = [('first_name', 'last_name'),
                    ('Bill', 'Rodgers'),
                    ('Bob', 'Kennedy')]
            for n, athlete in enumerate(rows):
                sheet.write(n, 0, athlete[0])
                sheet.write(n, 1, athlete[1])
            book.save(_data)
            _data.seek(0)
            data = {'file': [_data]}
            roster = roster_upload_validator(data)
            self.assertEqual(roster,
                             [dict(zip(rows[0], rows[1])),
                              dict(zip(rows[0], rows[2]))])

    def test_roster_invalid_format(self):
        """Test that invalid file types raises an error."""
        with tempfile.NamedTemporaryFile(suffix='.pdf') as _data:
            data = {'file': [_data]}
            with self.assertRaises(ValidationError):
                roster = roster_upload_validator(data)

    def test_roster_invalid_headers(self):
        """Test that invalid headers raises an error."""
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='r+w') as _data:
            _data.write('first_name,middle_name\nSteve,Prefontaine')
            _data.seek(0)
            data = {'file': [_data]}
            with self.assertRaises(ValidationError):
                roster = roster_upload_validator(data)
