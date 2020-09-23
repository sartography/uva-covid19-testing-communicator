from communicator import db
from communicator.models.notification import Notification


class Sample(db.Model):
    barcode = db.Column(db.String, primary_key=True)
    student_id = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    location = db.Column(db.Integer)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    result_code = db.Column(db.String)
    in_firebase = db.Column(db.Boolean, default=False)  # Does this record exist in Firebase?
    in_ivy = db.Column(db.Boolean, default=False)  # Has this record come in from the IVY?
    email_notified = db.Column(db.Boolean, default=False)
    text_notified = db.Column(db.Boolean, default=False)
    notifications = db.relationship(Notification, back_populates="sample",
                                    cascade="all, delete, delete-orphan",
                                    order_by=Notification.date)

    def merge(self, sample):
        if sample.phone:
            self.phone = sample.phone
        if sample.email:
            self.email = sample.email
        if sample.result_code:
            self.result_code = sample.result_code
        if sample.in_firebase:
            self.in_firebase = True
        if sample.in_ivy:
            self.in_ivy = True

