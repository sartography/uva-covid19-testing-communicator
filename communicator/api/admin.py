from communicator import db, app
from communicator.models import Sample
from communicator.models.invitation import Invitation
from communicator.models.notification import Notification, EMAIL_TYPE, TEXT_TYPE
from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService
from time import sleep


def status():
    return {"status":"good"}

def add_sample(body):
    sample = Sample(barcode=body['barcode'],
                    student_id=body['student_id'],
                    date=body['date'],
                    location=body['location'])
    SampleService().add_or_update_records([sample])

def clear_samples():
    db.session.query(Notification).delete()
    db.session.query(Sample).delete()
    db.session.query(Invitation).delete()
    db.session.commit()


def update_and_notify():
    update_data()
    notify_by_email()
    notify_by_text()

def update_data():
    """Updates the database based on local files placed by IVY.  No longer attempts
    to pull files from the Firebase service."""
    ivy_service = IvyService()
    ivy_service.request_transfer()
    samples = ivy_service.load_directory()
    SampleService().add_or_update_records(samples)
    db.session.commit()

def merge_similar_records():
    sample_service = SampleService()
    sample_service.merge_similar_records()


def notify_by_email():
    """Sends out notifications via email"""
    samples = db.session.query(Sample)\
        .filter(Sample.result_code != None)\
        .filter(Sample.email_notified == False).all()
    with NotificationService(app) as notifier:
        for sample in samples:
            last_failure = sample.last_failure_by_type(EMAIL_TYPE)
            if last_failure: continue
            try:
                notifier.send_result_email(sample)
                sample.email_notified = True
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=True))
            except Exception as e:
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(0.5)


def notify_by_text():
    """Sends out notifications via SMS Message, but only at reasonable times of day"""
    with NotificationService(app) as notifier:
        if not notifier.is_reasonable_hour_for_text_messages:
            print("Skipping text messages, it's not a good time to get one.")
            return
        samples = db.session.query(Sample)\
            .filter(Sample.result_code != None)\
            .filter(Sample.text_notified == False).all()
        for sample in samples:
            last_failure = sample.last_failure_by_type(TEXT_TYPE)
            if last_failure: continue
            try:
                notifier.send_result_sms(sample)
                sample.text_notified = True
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=True))
            except Exception as e:
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(0.5)



