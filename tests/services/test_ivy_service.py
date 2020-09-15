import os
import unittest

from communicator import app
from tests.base_test import BaseTest

from communicator.errors import CommError
from communicator.services.ivy_service import IvyService


class IvyServiceTest(BaseTest):

    def test_read_file_and_build_records(self):
        records = IvyService.samples_from_ivy_file(self.ivy_file)
        self.assertEquals("987654321", records[0].student_id)
        self.assertEquals("testpositive@virginia.edu", records[1].email)
        self.assertEquals("1142270225", records[2].result_code)

    def test_invalid_file(self):
        with self.assertRaises(CommError):
            ivy_incorrect_file = os.path.join(app.instance_path, '..', 'tests', 'data', 'incorrect.csv')
            IvyService.samples_from_ivy_file(ivy_incorrect_file)

