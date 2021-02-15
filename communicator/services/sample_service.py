import re
from datetime import datetime

from sqlalchemy import func

from communicator import db, app
from communicator.models.sample import Sample
import random


class SampleService(object):
    """Handles the collection and syncing of data from various sources. """

    def add_or_update_records(self, samples):
        for sample in samples:
            existing = db.session.query(Sample).filter(Sample.barcode == sample.barcode).first()
            if existing is not None:
                existing.merge(sample)
                db.session.add(existing)
            else:
                db.session.add(sample)
        db.session.commit()


    def correct_computing_id(self):
        samples = db.session.query(Sample).\
            filter(func.coalesce(Sample.computing_id, '') == '').\
            filter(func.coalesce(Sample.email, '') != '').\
            all()
        email_match = re.compile('(.*).virginia.edu',  flags=re.IGNORECASE)
        for sample in samples:
            match = email_match.match(sample.email)
            if match:
                sample.computing_id = match.group(1).strip().lower()
        db.session.commit()

