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

    def split_all_location_columns(self):
        # Only fix records where the station isn't already set.
        # All stations prior to december 15th should be set to 1.
        date_time_str = 'DEC 12 2020 1:00AM'
        legacy_date = datetime.strptime(date_time_str, '%b %d %Y %I:%M%p')

        samples = db.session.query(Sample).\
            filter(Sample.station.is_(None)).all()
        for sample in samples:
            loc_code = str(sample.location)
            if sample.date < legacy_date:
                sample.station = sample.location
                sample.location = 1
            else:
                if len(loc_code) == 4:
                    sample.station = sample.location
                    sample.location = 1
                elif len(loc_code) == 3:
                    # more recent records, use the location provided.
                    location, station = int(loc_code[:1]), int(loc_code[1:])
                    sample.location = location
                    sample.station = station
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

