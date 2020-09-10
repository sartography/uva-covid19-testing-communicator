from communicator import db


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    phone = db.Column(db.String)
