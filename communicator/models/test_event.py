from communicator import db


class TestEvent(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, primary_key=True)
    location = db.Column(db.Integer)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    result_code = db.Column(db.String)
    notified = db.Column(db.Boolean, default=False)
    firebase_record = db.Column(db.Boolean, default=False)  # Does this record exist in Firebase?
    ivy_record = db.Column(db.Boolean, default=False)  # Has this record come in from the IVY?

    @classmethod
    def from_ivy_dict(cls, dictionary):
        """Creates a Test Result from a record read in from the IVY CSV File"""
        instance = cls()
        instance.student_id = dictionary["Student ID"]
        instance.phone = dictionary["Student Cellphone"]
        instance.email = dictionary["Student Email"]
        instance.date = dictionary["Test Date Time"]
        instance.location = dictionary["Test Kiosk Loc"]
        instance.result_code = dictionary["Test Result Code"]
        instance.from_ivy_dict = True
        return instance