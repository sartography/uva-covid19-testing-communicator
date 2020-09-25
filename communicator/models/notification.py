from sqlalchemy import func

from communicator import db

EMAIL_TYPE = "email"
TEXT_TYPE = "text"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    type = db.Column(db.String) # Either 'email' or 'text'
    successful = db.Column(db.Boolean)
    error_message = db.Column(db.String)
    sample_barcode = db.Column(db.String, db.ForeignKey('sample.barcode'), nullable=False)
    sample = db.relationship("Sample")

