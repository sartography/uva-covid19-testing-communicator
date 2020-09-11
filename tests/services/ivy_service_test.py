import unittest

from communicator.errors import CommError
from communicator.services.ivy_service import IvyService


class IvyServiceTest(unittest.TestCase):

    def test_read_file_and_build_records(self):
        data = IvyService.import_ivy_file('../data/results.csv')
        self.assertEquals(3, len(data))
        # Quick spot check on values
        self.assertEquals("987654321", data[0]["Student ID"])
        self.assertEquals("testpositive@virginia.edu", data[1]["Student Email"])
        self.assertEquals("1142270225", data[2]["Test Result Code"])
        records = []
        for d in data:
            records.append(IvyService.to_test_event_record(d))
        self.assertEquals("987654321", records[0].student_id)
        self.assertEquals("testpositive@virginia.edu", records[1].email)
        self.assertEquals("1142270225", records[2].result_code)

    def test_invalid_file(self):
        with self.assertRaises(CommError):
            data = IvyService.import_ivy_file('../data/incorrect.csv')
            records = []
            for d in data:
                records.append(IvyService.to_test_event_record(d))

