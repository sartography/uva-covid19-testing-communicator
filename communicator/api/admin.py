import smtplib
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

from communicator import db, app, executor
from communicator.models import Sample
from communicator.models.invitation import Invitation
from communicator.models.notification import Notification, EMAIL_TYPE, TEXT_TYPE
from communicator.models import Sample, SampleSchema
from communicator.models import IvyFile, IvyFileSchema
from communicator.models import Deposit, DepositSchema
from communicator.models.user import UserSchema
from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.sample_service import SampleService
from time import sleep

from communicator.services.user_service import UserService


def add_sample_search_filters(query, filters, ignore_dates=False):
    q_filters = dict()
    if "student_id" in filters:
        if (type(filters["student_id"]) == list):
            q_filters["student_id"] = or_(*[Sample.student_id == ID for ID in filters["student_id"]])

    if "location" in filters:
        if filters["location"] != None:
            q_filters["location"] = or_(*[Sample.location == ID for ID in filters["location"]])

    if "compute_id" in filters:
        if filters["compute_id"] != None:
            # Search Email and Compute ID column to account for typos 
            q_filters["compute_id"] = or_(*([Sample.computing_id.ilike(ID) for ID in filters["compute_id"]] + 
                                            [Sample.email.contains(ID.lower()) for ID in filters["compute_id"]]))
    if not ignore_dates:
        if "start_date" in filters:
            q_filters["start_date"] = Sample.date >= filters["start_date"]

        if "end_date" in filters:
            q_filters["end_date"] = Sample.date <= (filters["end_date"] + timedelta(1))
       
    if not "include_tests" in filters:
            q_filters["include_tests"] = Sample.student_id != 0

    query = query.filter(and_(*[q_filters[key] for key in q_filters]))
    return query


def verify_token(token, required_scopes):
    if token == app.config['API_TOKEN']:
        return {'scope':['any']}
    else:
        raise Exception("permission_denied", "API Token information is not correct")


def verify_admin(token, required_scopes):
    user_service = UserService()
    if user_service.is_valid_user():
        return {'scope':['any']}
    else:
        raise Exception("permission_denied", "You must be an admin user to call this endpoint.")


def get_user():
    user_service = UserService()
    return UserSchema().dump(user_service.get_user_info())


def add_sample(body):
    sample = Sample(barcode=body['barcode'],
                    student_id=body['student_id'],
                    computing_id=body['computing_id'],
                    date=body['date'])

    # Split the 4 digit location code into station and location
    loc_code = body['location']
    sample.location, sample.station = int(loc_code[:2]), int(loc_code[2:])

    SampleService().add_or_update_records([sample])


def get_samples(last_modified=None, created_on=None):
    query = db.session.query(Sample)
    if last_modified:
        lm_date = datetime.fromisoformat(last_modified)
        query = query.filter(Sample.last_modified > lm_date).order_by(Sample.last_modified)
    if created_on:
        co_date = datetime.fromisoformat(created_on)
        query = query.filter(Sample.created_on > co_date).order_by(Sample.created_on)
    else:
        query = query.order_by(Sample.created_on)

    samples = query.limit(200).all()
    response = SampleSchema(many=True).dump(samples)
    return response


def clear_samples():
    db.session.query(Notification).delete()
    db.session.query(Sample).delete()
    db.session.query(Invitation).delete()
    db.session.commit()

def clear_deposits():
    db.session.query(Deposit).delete()
    db.session.commit()

def get_deposits():
    query = db.session.query(Deposit)
    deposits = query.order_by(Deposit.date_added.desc()).all()
    response = DepositSchema(many=True).dump(deposits)
    return response

def add_deposit(body):
    from communicator.models.deposit import Deposit, DepositSchema
    
    new_deposit = Deposit(date_added=datetime.strptime(body['date_added'], "%m/%d/%Y").date(),
                      amount=int(body['amount']),
                      notes=body['notes'])

    db.session.add(new_deposit)
    db.session.commit()  
    return DepositSchema().dumps(new_deposit)   

def get_imported_files():
    from communicator.models.ivy_file import IvyFile, IvyFileSchema
    files = db.session.query(IvyFile).order_by(IvyFile.date_added.desc())
    return IvyFileSchema(many=True).dumps(files)

def get_deposits(page = "0"):
    query = db.session.query(Deposit)
    deposits = query.order_by(Deposit.date_added.desc())[int(page) * 10:(int(page) * 10) + 10]
    response = DepositSchema(many=True).dump(deposits)
    return response


def clear_deposits():
    db.session.query(Deposit).delete()
    db.session.commit()


def add_deposit(body):
    from communicator.models.deposit import Deposit, DepositSchema
    
    new_deposit = Deposit(date_added=datetime.strptime(body['date_added'], "%m/%d/%Y").date(),
                      amount=int(body['amount']),
                      notes=body['notes'])

    db.session.add(new_deposit)
    db.session.commit()  
    return DepositSchema().dumps(new_deposit)   


def get_imported_files(page = "0"):
    from sqlalchemy import func, case
    cases = [func.count(case([(Sample.email_notified == "t" , 1)])).label("successful_emails"),
            func.count(case([(Sample.email_notified == "f" , 1)])).label("failed_emails"),
            func.count(case([(Sample.text_notified == "t" , 1)])).label("successful_texts"),
            func.count(case([(Sample.text_notified == "f" , 1)])).label("failed_texts")]
    
    query = db.session.query(IvyFile.date_added,IvyFile.file_name,IvyFile.sample_count,
                *cases).order_by(IvyFile.date_added.desc()).join(Sample, Sample.ivy_file == '/ivy_data/outgoing/' + IvyFile.file_name)\
                .group_by(IvyFile.file_name)[int(page) * 10:(int(page) * 10) + 10]
    return query
    

def update_and_notify():
    # These can take a very long time to execute.
    executor.submit(_update_data)
    executor.submit(_notify_by_email)
    executor.submit(_notify_by_text)
    return "Task scheduled and running in the background"


def update_data():
    executor.submit(_update_data)
    return "Task scheduled and running in the background"


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
                assert (sample.email != None)
                notifier.send_result_email(sample)
                count += 1
                sample.email_notified = True
                db.session.add(Notification(type=EMAIL_TYPE, sample=sample, successful=True))
            except AssertionError as e:
                app.logger.error(f'Email not provided for Sample: {sample.barcode} ', exc_info=True)
                continue
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
