from tests.base_test import BaseTest

import json
from communicator.models import Sample
from communicator import db


class TestSampleEndpoint(BaseTest):

    sample_json = {"barcode": "000000111-202009091449-4321",
                   "location": "4321",
                   "date": "2020-09-09T14:49:00+0000",
                   "student_id": "000000111"}

    def test_create_sample(self):

        # Test add sample
        samples = db.session.query(Sample).all()
        self.assertEquals(0, len(samples))

        rv = self.app.post('/v1.0/sample',
                           content_type="application/json",
                           data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))

    def test_create_duplicate_sample_does_not_raise_error(self):

        # Test add sample
        samples = db.session.query(Sample).all()
        self.assertEquals(0, len(samples))

        rv = self.app.post('/v1.0/sample',content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample',content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample',content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample',content_type="application/json", data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))
