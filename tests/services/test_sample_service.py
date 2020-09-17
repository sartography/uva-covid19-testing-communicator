import json
import os
import unittest

from dateutil import parser

from tests.base_test import BaseTest
from communicator import db, app
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

