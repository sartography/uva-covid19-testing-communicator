import csv

from dateutil import parser

from communicator import app
from communicator.errors import CommError
from communicator.models.sample import Sample
from os import listdir
from os.path import isfile, join


class IvyService(object):
    """Opens files uploaded to the server from IVY and imports them into the database. """

    def __init__(self):
        self.path = app.config['IVY_IMPORT_DIR']

    def load_directory(self):
        onlyfiles = [f for f in listdir(self.path) if isfile(join(self.path, f))]
        samples = []
        for file in onlyfiles:
            samples.extend(IvyService.samples_from_ivy_file(join(self.path, file)))
        return samples

    @staticmethod
    def samples_from_ivy_file(file_name):
        rows = []
        with open(file_name, 'r') as csv_file:
            reader = csv.DictReader(csv_file, delimiter='|')
            for row in reader:
                sample = IvyService.record_to_sample(row)
                rows.append(sample)
        return rows

    @staticmethod
    def record_to_sample(dictionary):
        """Creates a Test Result from a record read in from the IVY CSV File"""
        sample = Sample()
        try:
            sample.barcode = f"{dictionary['Student ID']}-{dictionary['Test Date Time']}-{dictionary['Test Kiosk Loc']}"
            sample.student_id = dictionary["Student ID"]
            sample.phone = dictionary["Student Cellphone"]
            sample.email = dictionary["Student Email"]
            sample.date = parser.parse(dictionary["Test Date Time"])
            sample.location = dictionary["Test Kiosk Loc"]
            sample.result_code = dictionary["Test Result Code"]
            sample.in_ivy = True
            return sample
        except KeyError as e:
            raise CommError("100", f"Invalid CSV Record, missing column {e}")
