from communicator import db
from communicator.models.sample import Sample


class SampleService(object):
    """Handles the collection and syncing of data from various sources. """

    def add_or_update_records(self, samples):
        for sample in samples:
            existing = db.session.query(Sample).filter(Sample.barcode == sample.barcode).first()
            if existing is not None:
                existing.merge(sample)
            else:
                db.session.add(sample)
        db.session.commit()
