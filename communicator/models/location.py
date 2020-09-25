from communicator import db


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    firebase_id = db.Column(db.String)
    kiosks = db.relationship('Kiosk', back_populates="location")

class Kiosk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    location = db.relationship('Location')
