from tests.base_test import BaseTest
import os
import unittest
import globus_sdk

from communicator.models.ivy_file import IvyFile

from communicator import app, db

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

    def test_load_directory(self):
        self.assertEquals(0, db.session.query(IvyFile).count())
        app.config['IVY_IMPORT_DIR'] = os.path.join(app.root_path, '..', 'tests', 'data', 'import_directory')
        records = IvyService().load_directory(delete_from_globus=False)
        files = db.session.query(IvyFile).all()
        self.assertEquals(4, len(files))


