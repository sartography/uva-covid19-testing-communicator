import smtplib
from datetime import datetime

from communicator import db, app, executor
from communicator.models import Sample, Deposit, IvyFile
from communicator.models.invitation import Invitation

from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService
from time import sleep

from sqlalchemy import func

from communicator import db
import marshmallow
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from communicator.models.notification import Notification


class IvyFile(db.Model):
    file_name = db.Column(db.String, primary_key=True)
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    sample_count = db.Column(db.Integer)

class IvyFileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IvyFile
        load_instance = True
        include_relationships = True
        include_fk = True  # Includes foreign keys

def verify_token(token, required_scopes):
    if token == app.config['API_TOKEN']:
        return {'scope':['any']}
    else:
        raise Exception("permission_denied", "API Token information is not correct")


def status():
    return {"status": "good"}


def add_sample(body):
    sample = Sample(barcode=body['barcode'],
                    student_id=body['student_id'],
                    computing_id=body['computing_id'],
                    date=body['date'])

    # Split the 4 digit location code into station and location
    loc_code = body['location']
    sample.location, sample.station = int(loc_code[:2]), int(loc_code[2:])

    SampleService().add_or_update_records([sample])


def get_samples(last_modified=None):
    query = db.session.query(Sample)
    if last_modified:
        lm_date = datetime.fromisoformat(last_modified)
        query = query.filter(Sample.last_modified > lm_date)
    samples = query.order_by(Sample.last_modified).limit(200).all()
    response = SampleSchema(many=True).dump(samples)
    return response

def clear_samples():
    db.session.query(Notification).delete()
    db.session.query(Sample).delete()
    db.session.query(Invitation).delete()
    db.session.commit()

def get_deposits(last_modified=None):
    query = db.session.query(Sample)
    if last_modified:
        lm_date = datetime.fromisoformat(last_modified)
        query = query.filter(Sample.last_modified > lm_date)
    deposits = query.order_by(Deposit.date_added).all()
    response = DepositSchema(many=True).dump(deposits)
    return response

