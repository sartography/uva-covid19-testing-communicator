# Set environment variable to testing before loading.
# IMPORTANT - Environment must be loaded before app, models, etc....
import base64
import json
import os
import quopri
import re
import unittest
os.environ["TESTING"] = "true"

from communicator.models import Sample, Location, Kiosk
from communicator import app, db

import logging
logging.basicConfig()


class BaseTest(unittest.TestCase):
    """ Great class to inherit from, as it sets up and tears down classes
        efficiently when we have a database in place.
    """

    kiosks_file = os.path.join(app.root_path, '..', 'tests', 'data', 'kiosks.json')
    locations_file = os.path.join(app.root_path, '..', 'tests', 'data', 'locations.json')
    firebase_file = os.path.join(app.root_path, '..', 'tests', 'data', 'firebase_data.json')
    ivy_file = os.path.join(app.root_path, '..', 'tests', 'data', 'results.csv')


    if not app.config['TESTING']:
        raise (Exception("INVALID TEST CONFIGURATION. This is almost always in import order issue."
                         "The first class to import in each test should be the base_test.py file."))


    @classmethod
    def setUpClass(cls):
        app.config.from_object('config.testing')
        cls.ctx = app.test_request_context()
        cls.app = app.test_client()
        cls.ctx.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()
        db.drop_all()
        pass

    def setUp(self):
        pass

    def tearDown(self):
        db.session.query(Sample).delete()
        db.session.query(Kiosk).delete()
        db.session.query(Location).delete()
        db.session.commit()

    def decode(self, encoded_words):
        """
        Useful for checking the content of email messages
        (which we store in an array for testing)
        """
        encoded_word_regex = r'=\?{1}(.+)\?{1}([b|q])\?{1}(.+)\?{1}='
        charset, encoding, encoded_text = re.match(encoded_word_regex,
                                                   encoded_words).groups()
        if encoding == 'b':
            byte_string = base64.b64decode(encoded_text)
        elif encoding == 'q':
            byte_string = quopri.decodestring(encoded_text)
        text = byte_string.decode(charset)
        text = text.replace("_", " ")
        return text

    def load_example_data(self):
        self.load_example_locations()
        self.load_example_kiosks()

    def load_example_locations(self):
        with open(self.locations_file, 'r') as f:
            raw_data = json.load(f)
            for d in raw_data:
                new_loc = Location(id=d['id'], firebase_id=d['firebase_id'], name=d['name'])
                db.session.add(new_loc)
                db.session.commit()

            locs = db.session.query(Location).all()
            self.assertEqual(len(raw_data), len(locs))

    def load_example_kiosks(self):
        with open(self.kiosks_file, 'r') as f:
            raw_data = json.load(f)
            for d in raw_data:
                new_kiosk = Kiosk(id=d['id'], location_id=d['location_id'])
                db.session.add(new_kiosk)
                db.session.commit()

            kiosks = db.session.query(Kiosk).all()
            self.assertEqual(len(raw_data), len(kiosks))
