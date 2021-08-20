import datetime

import pytz

from tests.base_test import BaseTest
import os
import unittest
import globus_sdk

from communicator import app, db

from communicator.models.ivy_file import IvyFile

from communicator.errors import CommError
from communicator.services.ivy_service import IvyService


class IvyServiceTest(BaseTest):

    def test_read_file_and_build_records(self):
        records = IvyService.samples_from_ivy_file(self.ivy_path, self.ivy_file)
        self.assertEqual("987654321", records[0].student_id)
        self.assertEqual("testpositive@virginia.edu", records[1].email)
        self.assertEqual("1142270225", records[2].result_code)

    def test_invalid_file(self):
        with self.assertRaises(CommError):
            ivy_incorrect_path = os.path.join(app.root_path, '..', 'tests', 'data')
            IvyService.samples_from_ivy_file(ivy_incorrect_path, 'incorrect.csv')

    def test_invalid_date(self):
        """If a record with an unparssable date comes through, use today's date in the date field."""
        ivy_incorrect_path = os.path.join(app.root_path, '..', 'tests', 'data')
        records = IvyService.samples_from_ivy_file(ivy_incorrect_path,  'incorrect_date.csv')
        self.assertEquals(4, len(records))
        self.assertEquals('987655321-TN-20212719-4321', records[2].barcode)

    def test_timezone_offset(self):
        """The date and time returned from the lab / Globus is in EST, be sure to save it as such to
        avoid a 5 hour offset, when it is assumed to be in GMT."""
        records = IvyService.samples_from_ivy_file(self.ivy_path, self.ivy_file)
        self.assertEqual("987654321", records[0].student_id)
        self.assertIsNotNone(records[0].date.tzinfo, "on ingestion, the date should be in EST")

        # original date "202009030809"
        date_string = '202009031209' # UTC is 4 hours head for this date
        date = datetime.datetime.strptime(date_string, '%Y%m%d%H%M')

        db.session.add(records[0])
        db.session.commit()
        self.assertEqual(date, records[0].date)


    def test_load_directory(self):
        self.assertEqual(0, db.session.query(IvyFile).count())
        app.config['IVY_IMPORT_DIR'] = os.path.join(app.root_path, '..', 'tests', 'data', 'import_directory')
        files, _ = IvyService().load_directory()
        self.assertEqual(4, len(files))


