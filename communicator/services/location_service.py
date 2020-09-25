from communicator import db
from communicator.errors import CommError
from communicator.models import Sample
from communicator.models.location import Location, Kiosk


class LocationService(object):
    """Handles the collection and syncing of data from various sources. """

    def add_or_update_locations(self, locations):
        for location in locations:
            existing = db.session.query(Location).filter(Location.id == location.id).first()
            if existing is not None:
                existing.merge(location)
            else:
                db.session.add(location)
        db.session.commit()

    def add_or_update_kiosks_for_location(self, location_id, num_kiosks):
        kiosks = db.session.query(Kiosk).filter(Kiosk.location_id == location_id).order_by(Kiosk.id).all()

        max_id = max(k.id for k in kiosks)

        # New max id will be location_id x 100 + num_kiosks
        # e.g. if location_id is 2 and we want 4 kiosks, the new max
        # kiosk id will be 204. Obviously, we'll max out at 99 kiosks per
        # location, but we'll burn that bridge when we get there.
        new_max_id = location_id * 100 + num_kiosks

        if len(kiosks) > num_kiosks:
            # Remove kiosks if no samples are found in the database for this kiosk.
            samples = db.session.query(Sample)\
                .filter(Sample.location_id == location_id)\
                .filter(Sample.kiosk_id >= num_kiosks).count()

            if len(samples) > 0:
                raise CommError(100, 'Cannot remove kiosks that still have pending samples.')

            # Remove the kiosks with ids higher than num_kiosk
            for i in range(max_id, new_max_id + 1):
                db.session.query(Kiosk).filter(Kiosk.id == i + 1).delete()
            db.session.commit()

        elif len(kiosks) < num_kiosks:
            # Increment max_id, then create kiosks up to the new max.
            for i in range(max_id, new_max_id + 1):
                new_kiosk = Kiosk(id=i + 1, location_id=location_id)
                db.session.add(new_kiosk)
            db.session.commit()

