from communicator import db


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    type = db.Column(db.String) # Either 'email' or 'text'
    successful = db.Column(db.Boolean)
    error_message = db.Column(db.String)
    sample_barcode = db.Column(db.String, db.ForeignKey('sample.barcode'), nullable=False)
    sample = db.relationship("Sample")
