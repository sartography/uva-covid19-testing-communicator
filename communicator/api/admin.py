from operator import or_

from communicator import db, app
from communicator.errors import ApiError, CommError
from communicator.models import Sample
from communicator.services.firebase_service import FirebaseService
from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService


def status():
    return {"status":"good"}

def add_sample(body):
    sample = Sample(barcode=body['barcode'],
                    student_id=body['student_id'],
                    date=body['date'],
                    location=body['location'])
    db.session.add(sample)
    db.session.commit()

def clear_samples():
    db.session.query(Sample).delete()
    db.session.commit()

def update_data():
    """Updates the database based on local files placed by IVY.  No longer attempts
    to pull files from the Firebase service."""
    ivy_service = IvyService()

    samples = ivy_service.load_directory()
    SampleService().add_or_update_records(samples)
    db.session.commit()


def notify_by_email():
    """Sends out notifications via email"""

    samples = db.session.query(Sample)\
        .filter(Sample.result_code != None)\
        .filter(Sample.email_notified == False).all()
    notifier = NotificationService(app)
    for sample in samples:
        try:
            notifier.send_result_email(sample)
            sample.email_notified = True
        except CommError as ce:
            print("Error")





