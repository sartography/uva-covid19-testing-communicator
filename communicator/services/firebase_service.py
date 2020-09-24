import json

from google.cloud import firestore
from google.oauth2 import service_account

from communicator import app
from communicator.models.sample import Sample


class FirebaseService(object):
    """Connects to the Google's Firecloud service to retrieve any records added by the tablets. """

    def __init__(self):
        json_config = json.loads(app.config['FIRESTORE_JSON'])
        credentials = service_account.Credentials.from_service_account_info(json_config)
        self.db = firestore.Client(project="uva-covid19-testing-kiosk",
                                   credentials= credentials)

    def get_samples(self):
        # Then query for documents
        fb_samples = self.db.collection(u'samples')
        samples = []
        for s in fb_samples.stream():
            samples.append(FirebaseService.record_to_sample(s))
        return samples

    @staticmethod
    def record_to_sample(fb_sample):
        sample = Sample()
        dictionary = fb_sample.to_dict()
        sample.barcode = dictionary["id"]
        sample.student_id = dictionary["barcodeId"]
        sample.date = dictionary["createdAt"]
        sample.location = dictionary["locationId"]
        sample.in_firebase = True
        return sample
