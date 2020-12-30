import smtplib

from communicator import db, app, executor
from communicator.models import Sample
from communicator.models.invitation import Invitation
from communicator.models.notification import Notification, EMAIL_TYPE, TEXT_TYPE
from communicator.models.sample import SampleSchema
from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService
from time import sleep


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
                    date=body['date'],
                    location=body['location'])
    SampleService().add_or_update_records([sample])


def get_samples(bar_code=None):
    query = db.session.query(Sample)
    if bar_code:
        last_sample = db.session.query(Sample).filter(Sample.barcode == bar_code).first()
        if not last_sample:
            app.logger.error(f'Someone queried for a barcode that does not exist: {bar_code} ', exc_info=True)
            raise Exception("No such bar code.")
        query = query.filter(Sample.date > last_sample.date)
    samples = query.order_by(Sample.date).limit(200).all()
    response = SampleSchema(many=True).dump(samples)
    return response



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
    app.logger.info("Executing Update Data Task")
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

def split_location_column():
    sample_service = SampleService()
    sample_service.split_location_column()
    
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
    count = 0
    with NotificationService(app) as notifier:
        for sample in samples:
            last_failure = sample.last_failure_by_type(EMAIL_TYPE)
            if last_failure and not retry:
                continue
            try:
                notifier.send_result_email(sample)
                count += 1
                sample.email_notified = True
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=True))
            except smtplib.SMTPServerDisconnected as de:
                app.logger.error("Database connection terminated, stopping for now.", exc_info=True)
                break
            except smtplib.SMTPResponseException as re:
                if re.smtp_code == 451:
                    app.logger.error("Too many messages error from SMTP Service, stopping for now.", exc_info=True)
                    break
                else:
                    app.logger.error(f'An exception happened in EmailService sending to {sample.email} ', exc_info=True)
                    app.logger.error(str(e))
                    db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=False,
                                                error_message=str(e)))
            except Exception as e:
                app.logger.error(f'An exception happened in EmailService sending to {sample.email} ', exc_info=True)
                app.logger.error(str(e))
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(0.5)
            if count > 190:  # At 2 a second, it should take 80 seconds or around a minute and 1/2 to send out a set.
                app.logger.info("Reached the max 190 messages, stopping for now.")
                break



def notify_by_text(file_name=None, retry=False):
    executor.submit(_notify_by_text, file_name, retry)
    return "Task scheduled and running the background"


def _notify_by_text(file_name=None, retry=False):
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

        # Do not limit texts, as errors pile up we end up sending less and less, till none go out.
        # sample_query = sample_query.limit(150)  # Only send out 150 texts at a time.
        samples = sample_query.all()
        count = 0
        for sample in samples:
            last_failure = sample.last_failure_by_type(TEXT_TYPE)
            if last_failure and not retry:
                continue
            try:
                notifier.send_result_sms(sample)
                count += 1
                sample.text_notified = True
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=True))
            except Exception as e:
                db.session.add(Notification(type=TEXT_TYPE, sample=sample, successful=False,
                                            error_message=str(e)))
            db.session.commit()
            sleep(0.5)
            if count > 190:
                break
