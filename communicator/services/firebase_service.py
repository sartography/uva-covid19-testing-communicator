import os


from google.cloud import firestore

from communicator import app
from communicator.models.sample import Sample


class FirebaseService(object):
    """Connects to the Google's Firecloud service to retrieve any records added by the tablets. """

    def __init__(self):
        resource_path = os.path.join(app.instance_path, 'firestore_service_key.json')
        self.db = firestore.Client.from_service_account_json(resource_path)

    def get_samples(self):
        # Then query for documents
        samples = self.db.collection(u'samples')
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
