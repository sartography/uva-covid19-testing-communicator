import re

from flask_table import Table, Col, LinkCol, BoolCol, DatetimeCol, NestedTableCol
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, IntegerField, BooleanField, SelectField, validators, HiddenField, TextAreaField, \
    ValidationError
from wtforms.widgets import TextArea


class InvitationForm(FlaskForm):
    location = StringField('Location (ex. Newcomb Hall, South Meeting Room)', [validators.DataRequired()])
    date = StringField('Date (ex. Monday, September 23 from 10:00 am-5:00 pm ', [validators.DataRequired()])
    emails = TextAreaField('Emails (newline delimited)', render_kw={'rows': 10, 'cols': 50})

    def validate_emails(form, field):
        all_emails = field.data.splitlines()
        EMAIL_REGEX = re.compile('^[a-z0-9]+[._a-z0-9]+[@]\w+[.]\w{2,3}$')
        for email in all_emails:
            if not re.search(EMAIL_REGEX, email):
                raise ValidationError(f'Invalid email \'{email}\', Emails must each be on a seperate line.')


class LocationForm(FlaskForm):
    id = IntegerField('ID #', [validators.DataRequired()])
    firebase_id = StringField('Value of @id field in Firebase database (ex. https://www.virginia.edu/newcomb-covid-testing)', [validators.DataRequired()])
    name = StringField('Display name of location (ex. Newcomb Hall South Meeting Room)', [validators.DataRequired()])
