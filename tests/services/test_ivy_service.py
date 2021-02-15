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
        records = IvyService.samples_from_ivy_file(self.ivy_file)
        self.assertEqual("987654321", records[0].student_id)
        self.assertEqual("testpositive@virginia.edu", records[1].email)
        self.assertEqual("1142270225", records[2].result_code)

    def test_invalid_file(self):
        with self.assertRaises(CommError):
            ivy_incorrect_file = os.path.join(app.root_path, '..', 'tests', 'data', 'incorrect.csv')
            IvyService.samples_from_ivy_file(ivy_incorrect_file)

    def test_invalid_date(self):
        """If a record with an unparssable date comes through, use today's date in the date field."""
        ivy_incorrect_file = os.path.join(app.root_path, '..', 'tests', 'data', 'incorrect_date.csv')
        records = IvyService.samples_from_ivy_file(ivy_incorrect_file)
        self.assertEquals(4, len(records))
        self.assertEquals('987655321-TN-20212719-4321', records[2].barcode)

    def test_load_directory(self):
        self.assertEqual(0, db.session.query(IvyFile).count())
        app.config['IVY_IMPORT_DIR'] = os.path.join(app.root_path, '..', 'tests', 'data', 'import_directory')
        files, _ = IvyService().load_directory()
        self.assertEqual(4, len(files))


