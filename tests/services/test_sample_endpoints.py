from datetime import datetime
from time import sleep

from tests.base_test import BaseTest

import json
from communicator.models import Sample
from communicator import db, app
from communicator.api import admin
from communicator.models.notification import Notification


class TestSampleEndpoint(BaseTest):
    sample_json = {"barcode": "000000111-202009091449-4321",
                   "location": "0102",
                   "date": "2020-09-09T14:49:00+0000",
                   "student_id": "000000111",
                   "computing_id": "abc12d"}

    def test_create_sample(self):
        # Test add sample
        samples = db.session.query(Sample).all()
        self.assertEquals(0, len(samples))

        rv = self.app.post('/v1.0/sample',
                           content_type="application/json",
                           data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))

    def test_create_sample_gets_correct_location_and_station(self):
        # Test add sample
        samples = db.session.query(Sample).all()
        self.assertEquals(0, len(samples))

        rv = self.app.post('/v1.0/sample',
                           content_type="application/json",
                           data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))
        self.assertEquals(1, samples[0].location)
        self.assertEquals(2, samples[0].station)

    def test_create_sample_has_last_updated(self):
        rv = self.app.post('/v1.0/sample',
                           content_type="application/json",
                           data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))
        self.assertIsNotNone(samples[0].last_modified)

    def test_create_duplicate_sample_does_not_raise_error(self):
        # Test add sample
        samples = db.session.query(Sample).all()
        self.assertEquals(0, len(samples))

        rv = self.app.post('/v1.0/sample', content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample', content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample', content_type="application/json", data=json.dumps(self.sample_json))
        rv = self.app.post('/v1.0/sample', content_type="application/json", data=json.dumps(self.sample_json))

        samples = db.session.query(Sample).all()
        self.assertEquals(1, len(samples))

    def test_notify_by_email_by_file_name(self):
        db.session.add(Sample(barcode="000000111-202009091449-4321",
                              location="4321",
                              date="2020-09-09T14:49:00+0000",
                              student_id="000000111",
                              email="daniel.h.funk@gmail.com",
                              result_code="12345",
                              ivy_file="xxx"))
        db.session.add(Sample(barcode="000000112-202009091449-4321",
                              location="4321",
                              date="2020-09-09T14:49:00+0000",
                              student_id="000000112",
                              email="dan@gmail.com",
                              result_code="12345",
                              ivy_file="yyy"))
        db.session.commit()
        admin._notify_by_email('xxx')
        samples = db.session.query(Sample).filter(Sample.email_notified == True).all()
        self.assertEquals(1, len(samples))
        samples = db.session.query(Sample).filter(Sample.email_notified != True).all()
        self.assertEquals(1, len(samples))
        admin._notify_by_email()
        samples = db.session.query(Sample).filter(Sample.email_notified == True).all()
        self.assertEquals(2, len(samples))

    def test_get_all_samples(self):
        s1 = Sample(barcode="000000111-202009091449-4321",
                    location="4321",
                    date= datetime.now(),
                    student_id="000000111",
                    email="daniel.h.funk@gmail.com",
                    result_code="12345",
                    ivy_file="xxx",
                    email_notified=True,
                    text_notified=True)
        s2 = Sample(barcode="000000112-202009091449-4321",
                    location="4321",
                    date= datetime.now(),
                    student_id="000000112",
                    email="dan@gmail.com",
                    result_code="12345",
                    ivy_file="yyy",
                    email_notified=False,
                    text_notified=False)
        db.session.add(s1)
        db.session.add(Notification(sample=s1, date="2020-12-09T14:49:00+0000", type="email", successful=True))
        db.session.add(Notification(sample=s1, date="2020-12-09T14:49:00+0000", type="text", successful=True))
        db.session.add(s2)

        rv = self.app.get('/v1.0/sample', content_type="application/json",
                          headers={'X-CR-API-KEY': app.config.get('API_TOKEN')})
        data = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(data))
        self.assertEqual("000000111-202009091449-4321", data[0]["barcode"])
        self.assertEqual(2, len(data[0]["notifications"]))
        self.assertEqual(True, data[0]['email_notified'])
        self.assertEqual(True, data[0]["notifications"][0]["successful"])

        self.assertEqual(0, len(data[1]["notifications"]))
        self.assertEqual(False, data[1]['email_notified'])

        print(data)


    def test_get_all_samples_by_last_modified(self):
        d1_str = '202012300101' # dec 30th 2020
        d1 = datetime.strptime(d1_str, '%Y%m%d%H%M')
        s1_bar_code = '000000111-'+ d1_str +'-4321'

        d2_str = '202101010101' # Jan 1st 2021
        d2 = datetime.strptime(d2_str, '%Y%m%d%H%M')
        s2_bar_code = '000000111-'+ d2_str +'-4321'

        s1 = Sample(barcode=s1_bar_code,
                    location="4321",
                    date= datetime.now(),
                    last_modified=d1,
                    student_id="000000111",
                    email="daniel.h.funk@gmail.com",
                    result_code="12345",
                    ivy_file="xxx",
                    email_notified=True,
                    text_notified=True)
        s2 = Sample(barcode=s2_bar_code,
                    location="4321",
                    date= datetime.now(),
                    last_modified=d2,
                    student_id="000000112",
                    email="dan@gmail.com",
                    result_code="12345",
                    ivy_file="yyy",
                    email_notified=False,
                    text_notified=False)
        db.session.add(s1)
        db.session.add(s2)

        rv = self.app.get(f'/v1.0/sample', content_type="application/json",
                          headers={'X-CR-API-KEY': app.config.get('API_TOKEN')})
        data = json.loads(rv.get_data(as_text=True))
        self.assertEquals(2, len(data))

        last_modified_arg = d1.isoformat()
        rv = self.app.get(f'/v1.0/sample?last_modified={last_modified_arg}', content_type="application/json",
                          headers={'X-CR-API-KEY': app.config.get('API_TOKEN')})
        data = json.loads(rv.get_data(as_text=True))
        self.assertEquals(1, len(data))
        self.assertEquals(s2.barcode, data[0]['barcode'])

        last_modified_arg = d2.isoformat()
        rv = self.app.get(f'/v1.0/sample?last_modified={last_modified_arg}', content_type="application/json",
                          headers={'X-CR-API-KEY': app.config.get('API_TOKEN')})
        data = json.loads(rv.get_data(as_text=True))
        self.assertEquals(0, len(data))
