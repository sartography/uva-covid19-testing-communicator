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

    def split_location_column(self):
        samples = db.session.query(Sample).filter(Sample.station == None).all()
        for sample in samples:
            loc_code = str(sample.location)
            if len(loc_code) == 4:
                location, station = int(loc_code[:2]), int(loc_code[2:])
                sample.location, sample.station = location, station
            elif len(loc_code) == 3:
                location, station = int(loc_code[:1]), int(loc_code[1:])
                sample.location, sample.station = location, station
        db.session.commit()

    def merge_similar_records(self):
        """ We have samples that are duplicates of each other because of the way the data was coming in
        earlier on.  This is a onetime fix that will compare all records based on the studient id, location
        and date, and merge them together using the new and correct bar code."""

        # Get all samples that do not contain an email (these were added via the api call)
        samples = db.session.query(Sample).filter(Sample.email == None).all()
        for sample in samples:
            sample2 = db.session.query(Sample).\
                filter(Sample.email != None).\
                filter(Sample.student_id == sample.student_id).\
                filter(Sample.date == sample.date).\
                filter(Sample.location == sample.location).\
                first()
            if sample2:
                sample.merge(sample2)
                # Move notifications over as well.
                notifications = sample2.notifications
                sample.notifications = notifications
                sample2.notifications = []
                db.session.add(sample)
                db.session.delete(sample2)
        db.session.commit()



