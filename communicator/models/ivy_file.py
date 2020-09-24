from sqlalchemy import func

from communicator import db


class IvyFile(db.Model):
    file_name = db.Column(db.String, primary_key=True)
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    sample_count = db.Column(db.Integer)
