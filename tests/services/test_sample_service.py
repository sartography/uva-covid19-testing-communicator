from datetime import datetime

from tests.base_test import BaseTest
import json

from dateutil import parser

from communicator.models.notification import Notification
from communicator import db
from communicator.models.sample import Sample
from communicator.services.ivy_service import IvyService
from communicator.services.sample_service import SampleService


class IvyServiceTest(BaseTest):

    def get_firebase_records(self):
        with open(self.firebase_file, 'r') as fb_file:
            raw_data = json.load(fb_file)
            samples = []
            for d in raw_data:
                samples.append(Sample(barcode=d['id'],
                                      student_id=d['barcodeId'],
                                      date=parser.parse(d['createdAt']),
                                      location=d['locationId'],
                                      in_firebase=True))
            return samples


    def test_correlate_samples_firebase_first(self):
        """Load up all the samples from firebase, then load data from ivy, and assure we
        get the correct number of records with the right details."""

        # Load firebase records
        service = SampleService()
        fb_samples = self.get_firebase_records()
        self.assertEqual(0, len(db.session.query(Sample).all()))

        service.add_or_update_records(fb_samples)

        self.assertEqual(4, len(db.session.query(Sample).all()))

        ivy_samples = IvyService.samples_from_ivy_file(self.ivy_file)
        service.add_or_update_records(ivy_samples)

        # There are 6 records in ivy, but three records that should match up, giving seven total
        self.assertEqual(6, len(db.session.query(Sample).filter(Sample.in_ivy == True).all()))
        self.assertEqual(4, len(db.session.query(Sample).filter(Sample.in_firebase == True).all()))
        self.assertEqual(3, len(db.session.query(Sample).filter(Sample.in_firebase == True)
                                 .filter(Sample.in_ivy == True).all()))
        self.assertEqual(7, len(db.session.query(Sample).all()))


    def test_correlate_samples_ivy_first(self):
        service = SampleService()

        self.assertEqual(0, len(db.session.query(Sample).all()))

        ivy_samples = IvyService.samples_from_ivy_file(self.ivy_file)
        service.add_or_update_records(ivy_samples)
        self.assertEqual(6, len(db.session.query(Sample).all()))

        fb_samples = self.get_firebase_records()
        service.add_or_update_records(fb_samples)

        self.assertEqual(6, len(db.session.query(Sample).filter(Sample.in_ivy == True).all()))
        self.assertEqual(4, len(db.session.query(Sample).filter(Sample.in_firebase == True).all()))
        self.assertEqual(3, len(db.session.query(Sample).filter(Sample.in_firebase == True)
                                 .filter(Sample.in_ivy == True).all()))
        self.assertEqual(7, len(db.session.query(Sample).all()))


    def test_merge_similar_records(self):
        service = SampleService()
#        511908685 - 202010051136 - 0202
        s1 = Sample(barcode="111111111-AAA-202010050000-0000",
                              student_id=111111111,
                              date = parser.parse("202010050000"),
                              last_modified = parser.parse("202010050000"),
                              location=0)
        s2 = Sample(barcode="111111111-202010050000-0000",
                              student_id=111111111,
                              date = parser.parse("202010050000"),
                              last_modified = parser.parse("202010050000"),
                              location=0,
                              email="dan@sartography.com",
                              phone="555-555-5555")
        s2n = Notification(date=parser.parse("202010050000"), type="email", successful=True)
        s2.notifications = [s2n]
        db.session.add(s1)
        db.session.add(s2)
        db.session.commit()

        delta = datetime.now() - s1.last_modified
        self.assertGreater(delta.days, 1) # Last modified is in the past.

        self.assertEquals(2, len(db.session.query(Sample).all()))
        service.merge_similar_records()
        self.assertEquals(1, len(db.session.query(Sample).all()))
        sample = db.session.query(Sample).first()
        self.assertEquals("dan@sartography.com", sample.email)
        self.assertEquals("111111111-AAA-202010050000-0000", sample.barcode)
        self.assertEquals(1, len(sample.notifications))
        delta = datetime.now() - sample.last_modified
        self.assertEquals(0, delta.days) # Last modified is updated on merge.

    def test_merge_non_similar_records(self):
        service = SampleService()
        db.session.add(Sample(barcode="222222222-AAA-202010050000-0000",
                              student_id=222222222,
                              date = parser.parse("202010050000"),
                              location=0))
        db.session.add(Sample(barcode="111111111-202010050000-0000",
                              student_id=111111111,
                              date = parser.parse("202010050000"),
                              location=0,
                              email="dan@sartography.com",
                              phone="555-555-5555"))
        service.merge_similar_records()
        self.assertEquals(2, len(db.session.query(Sample).all()))


    def test_correct_computing_id(self):
        service = SampleService()
        db.session.add(Sample(barcode="222222222-AAA-202010050000-0000",
                              student_id=222222222,
                              email="dhf8r@virginia.edu",
                              date = parser.parse("202010050000"),
                              location=0))
        db.session.add(Sample(barcode="333333333-AAA-202010050000-0000",
                              student_id=333333333,
                              email="dhf8r@VIRGINIA.edu",
                              date = parser.parse("202010050000"),
                              location=0))
        db.session.add(Sample(barcode="444444444-AAA-202010050000-0000",
                              student_id=444444444,
                              computing_id="dhf8r",
                              email="xxxxx@VIRGINIA.edu",
                              date = parser.parse("202010050000"),
                              location=0))
        db.session.add(Sample(barcode="555555555-AAA-202010050000-0000",
                              student_id=555555555,
                              email="    dhf8r@VIRGINIA.edu   ",
                              date = parser.parse("202010050000"),
                              location=0))

        service.correct_computing_id()
        samples = db.session.query(Sample).all()
        for s in samples:
            self.assertEqual("dhf8r", s.computing_id)

