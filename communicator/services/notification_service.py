import smtplib
import uuid
from datetime import datetime, time, date
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from os.path import join

import dateutil
import phonenumbers
import pytz
from flask import render_template
from pytz import timezone
from twilio.rest import Client

from communicator import app, db
from communicator.errors import CommError
from communicator.models.invitation import Invitation

TEST_MESSAGES = []


class NotificationService(object):
    """Provides common tools for working with email and text messages, please use this
    using the "with" syntax, to assure connections are properly closed.
    ex:

    with NotificationService() as notifier:
        notifier.send_result_email(sample)
        notifier.send_result_text(sample)

    """

    def __init__(self, app):
        self.app = app
        self.sender = app.config['MAIL_SENDER']
        self.URL_ROOT = app.config['URL_ROOT']

    def __enter__(self):
        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            return self
        self.email_server = self._get_email_server()
        self.twilio_client = self._get_twilio_client()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            return
        self.email_server.close()
        # No way to close the twilio client that I can see.

    def get_link(self, sample):
        return f"https://besafe.virginia.edu/result-demo?code={sample.result_code}"

    def send_result_sms(self, sample):
        link = self.get_link(sample)

        phone_number = phonenumbers.parse(sample.phone, "US")
        if not phonenumbers.is_valid_number(phone_number):
            raise CommError(6001, f"invalid phone number: {sample.phone}")
        phone_number_string = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
        if sample.email and '@' in sample.email:
            name = sample.email.split('@')[0]
        else:
            name = "Student"

        message = f"Dear {name}, You have an important notification from UVA, please visit: {link}. " \
                  f"Reply 'STOP' to opt-out."

        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            TEST_MESSAGES.append(message)
        else:
            message = self.twilio_client.messages.create(
                to=phone_number_string,
                from_=self.app.config['TWILIO_NUMBER'],
                body=message)

    def send_result_email(self, sample):
        link = self.get_link(sample)
        subject = "UVA: BE SAFE Notification"
        tracking_code = self._tracking_code()
        text_body = render_template("result_email.txt",
                                    link=link,
                                    base_url=self.URL_ROOT,
                                    sample=sample,
                                    tracking_code=tracking_code)

        html_body = render_template("result_email.html",
                                    link=link,
                                    base_url=self.URL_ROOT,
                                    sample=sample,
                                    tracking_code=tracking_code)

        self._send_email(subject, recipients=[sample.email], text_body=text_body, html_body=html_body)

        return tracking_code

    def send_invitations(self, date, location, email_string):
        emails = email_string.splitlines()
        subject = "UVA: BE SAFE - Appointment"
        tracking_code = self._tracking_code()
        text_body = render_template("invitation_email.txt",
                                    date=date,
                                    location=location,
                                    base_url=self.URL_ROOT,
                                    tracking_code=tracking_code)

        html_body = render_template("invitation_email.html",
                                    date=date,
                                    location=location,
                                    base_url=self.URL_ROOT,
                                    tracking_code=tracking_code)

        self._send_email(subject, recipients=[self.sender], bcc=emails, text_body=text_body, html_body=html_body)

        invitation_log = Invitation(location=location, date=date, total_recipients=len(emails))
        db.session.add(invitation_log)
        db.session.commit()

    def _tracking_code(self):
        return str(uuid.uuid4())[:16]

    def _get_email_server(self):

        server = smtplib.SMTP(host=self.app.config['MAIL_SERVER'],
                              port=self.app.config['MAIL_PORT'],
                              timeout=self.app.config['MAIL_TIMEOUT'])
        server.ehlo()
        if self.app.config['MAIL_USE_TLS']:
            server.starttls()
        if self.app.config['MAIL_USERNAME']:
            server.login(self.app.config['MAIL_USERNAME'],
                         self.app.config['MAIL_PASSWORD'])
        return server

    def _get_twilio_client(self):
        return Client(self.app.config['TWILIO_SID'],
                      self.app.config['TWILIO_TOKEN'])

    def _send_email(self, subject, recipients, text_body, html_body, bcc=[], sender=None, ical=None):
        msgRoot = MIMEMultipart('related')
        msgRoot.set_charset('utf8')

        if sender is None:
            sender = self.sender

        msgRoot['Subject'] = Header(subject.encode('utf-8'), 'utf-8').encode()
        msgRoot['From'] = sender
        msgRoot['To'] = ', '.join(recipients)
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        part1 = MIMEText(text_body, 'plain', _charset='UTF-8')
        part2 = MIMEText(html_body, 'html', _charset='UTF-8')

        msgAlternative.attach(part1)
        msgAlternative.attach(part2)

        # Embed the logo image
        # This example assumes the image is in the current directory
        fp = open(join(app.root_path, 'static', 'uva_logo.png'), 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<logo>')
        msgRoot.attach(msgImage)

        # Leaving this on here, just in case we need it later.
        if ical:
            ical_atch = MIMEText(ical.decode("utf-8"), 'calendar')
            ical_atch.add_header('Filename', 'event.ics')
            ical_atch.add_header('Content-Disposition', 'attachment; filename=event.ics')
            msgRoot.attach(ical_atch)

        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            print("TEST:  Recording Emails, not sending - %s - to:%s" % (subject, recipients))
            TEST_MESSAGES.append(msgRoot)
            return

        all_recipients = recipients + bcc

        try:
            self.email_server.sendmail(sender, all_recipients, msgRoot.as_bytes())
        except Exception as e:
            app.logger.error('An exception happened in EmailService', exc_info=True)
            app.logger.error(str(e))
            raise CommError(5000, f"failed to send email to {', '.join(recipients)}", e)

    def is_reasonable_hour_for_text_messages(self):
        """Where 'reasaonable' is between 8am and 10pm. """
        tz = pytz.timezone('US/Eastern')
        now = (datetime.now(tz))
        eight_am = (datetime.now(tz).replace(hour=8, minute=0, second=0, microsecond=0))
        ten_pm = (datetime.now(tz).replace(hour=22, minute=0, second=0, microsecond=0))
        return eight_am <= now <= ten_pm
