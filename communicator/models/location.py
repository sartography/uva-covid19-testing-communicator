from communicator import db


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    firebase_id = db.Column(db.String)
    kiosks = db.relationship('Kiosk', back_populates="location")

    def merge(self, location):
        if location.name:
            self.name = location.name
        if location.firebase_id:
            self.firebase_id = location.firebase_id


class Kiosk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    location = db.relationship('Location')

    def merge(self, kiosk):
        if kiosk.location_id:
            self.location_id = kiosk.location_id
