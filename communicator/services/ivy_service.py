import csv

from communicator.errors import CommError
from communicator.models.test_event import TestEvent


class IvyService(object):

    @staticmethod
    def import_ivy_file(file_name):
        rows = []
        with open(file_name, 'r') as csv_file:
            reader = csv.DictReader(csv_file, delimiter='|')
            for row in reader:
                rows.append(row)
        return rows

    @staticmethod
    def to_test_event_record(data):
        try:
            return TestEvent.from_ivy_dict(data)
        except KeyError as e:
            raise CommError("100", f"Invalid CSV Record, missing column {e}");