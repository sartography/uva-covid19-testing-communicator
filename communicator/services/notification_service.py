import smtplib
import uuid
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import render_template
from flask_mail import Message

from communicator import db, mail, app
from communicator.errors import ApiError, CommError

TEST_MESSAGES = []

class NotificationService(object):
    """Provides common tools for working with an Email"""

    def __init__(self, app):
        self.app = app
        self.sender = app.config['MAIL_SENDER']

    def email_server(self):
        print("Server:" + self.app.config['MAIL_SERVER'])
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

    def tracking_code(self):
        return str(uuid.uuid4())[:16]

    def send_result_email(self, sample):
        subject = "UVA: BE SAFE Notification"
        link = f"https://besafe.virginia.edu/result-demo?code={sample.result_code}"
        tracking_code = self.tracking_code()
        text_body = render_template("result_email.txt",
                                    link=link,
                                    sample=sample,
                                    tracking_code=tracking_code)

        html_body = render_template("result_email.html",
                                    link=link,
                                    sample=sample,
                                    tracking_code=tracking_code)

        self.send_email(subject, recipients=[sample.email], text_body=text_body, html_body=html_body)

        return tracking_code



    def send_email(self, subject, recipients, text_body, html_body, sender=None, ical=None):
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

        # Leaving this on here, just in case we need it later.
        if ical:
            ical_atch = MIMEText(ical.decode("utf-8"),'calendar')
            ical_atch.add_header('Filename','event.ics')
            ical_atch.add_header('Content-Disposition','attachment; filename=event.ics')
            msgRoot.attach(ical_atch)

        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            print("TEST:  Recording Emails, not sending - %s - to:%s" % (subject, recipients))
            TEST_MESSAGES.append(msgRoot)
            return

        try:
            server = self.email_server()
            server.sendmail(sender, recipients, msgRoot.as_bytes())
            server.quit()
        except Exception as e:
            app.logger.error('An exception happened in EmailService', exc_info=True)
            app.logger.error(str(e))
            raise CommError(5000, f"failed to send email to {', '.join(recipients)}", e)

