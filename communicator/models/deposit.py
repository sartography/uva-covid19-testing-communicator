from sqlalchemy import func

from communicator import db

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    amount = db.Column(db.Integer)
    notes = db.Column(db.String)
