# Set environment variable to testing before loading.
# IMPORTANT - Environment must be loaded before app, models, etc....
import base64
import os
import quopri
import re
import unittest
os.environ["TESTING"] = "true"

from communicator.models import Sample


from communicator import app, db

import logging
logging.basicConfig()


class BaseTest(unittest.TestCase):
    """ Great class to inherit from, as it sets up and tears down classes
        efficiently when we have a database in place.
    """

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