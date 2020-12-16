from sqlalchemy import func

from communicator import db

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_sent = db.Column(db.DateTime(timezone=True), default=func.now())
    location = db.Column(db.String)
    date = db.Column(db.String)
    total_recipients = db.Column(db.Integer)
    coolness = db.Boolean()