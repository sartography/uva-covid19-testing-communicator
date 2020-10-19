from communicator import db, app, executor
from communicator.models import Sample
from communicator.models.invitation import Invitation
from communicator.models.notification import Notification, EMAIL_TYPE, TEXT_TYPE
from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService
from time import sleep


def status():
    return {"status": "good"}


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
    # These can take a very long time to execute.
    executor.submit(_update_data)
    executor.submit(_notify_by_email)
    executor.submit(_notify_by_text)
    return "Task scheduled and running the background"


def update_data():
    executor.submit(_update_data)
    return "Task scheduled and running the background"


def _update_data():
    """Updates the database based on local files placed by IVY.  No longer attempts
    to pull files from the Firebase service."""
    ivy_service = IvyService()
    ivy_service.request_transfer()
    files, samples = ivy_service.load_directory()
    SampleService().add_or_update_records(samples)
    for file in files:
        db.session.add(file)
        db.session.commit()
        if app.config['DELETE_IVY_FILES']:
            ivy_service.delete_file(file.file_name)
        else:
            app.logger.info("Not Deleting Files, per DELETE_IVY_FILES flag")
    db.session.commit()


def merge_similar_records():
    sample_service = SampleService()
    sample_service.merge_similar_records()


def notify_by_email(file_name=None, retry=False):
    executor.submit(_notify_by_email, file_name, retry)
    return "Task scheduled and running the background"


def _notify_by_email(file_name=None, retry=False):
    """Sends out notifications via email"""
    sample_query = db.session.query(Sample) \
        .filter(Sample.result_code != None) \
        .filter(Sample.email_notified == False)
    if file_name:
        sample_query = sample_query.filter(Sample.ivy_file == file_name)

    samples = sample_query.all()
    with NotificationService(app) as notifier:
        for sample in samples:
            last_failure = sample.last_failure_by_type(EMAIL_TYPE)
            if last_failure and not retry:
                continue
            try:
                notifier.send_result_email(sample)
                sample.email_notified = True
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=True))
            except Exception as e:
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(2)


def notify_by_text(file_name=None, retry=False):
    executor.submit(_notify_by_text, file_name, retry)
    return "Task scheduled and running the background"


def _notify_by_text(file_name, retry=False):
    """Sends out notifications via SMS Message, but only at reasonable times of day,
       Can be resticted to a specific file name, and will attempt to retry on previous
       failures if requested to do so. """
    with NotificationService(app) as notifier:
        if not notifier.is_reasonable_hour_for_text_messages:
            print("Skipping text messages, it's not a good time to get one.")
            return
        sample_query = db.session.query(Sample) \
            .filter(Sample.result_code != None) \
            .filter(Sample.text_notified == False)
        if file_name:
            sample_query = sample_query.filter(Sample.ivy_file == file_name)
        samples = sample_query.all()
        for sample in samples:
            last_failure = sample.last_failure_by_type(TEXT_TYPE)
            if last_failure and not retry:
                continue
            try:
                notifier.send_result_sms(sample)
                sample.text_notified = True
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=True))
            except Exception as e:
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(0.5)
