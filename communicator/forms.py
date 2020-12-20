import re

from flask_table import Table, Col, LinkCol, BoolCol, DatetimeCol, NestedTableCol
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, BooleanField, SelectField, validators, HiddenField, TextAreaField, \
    ValidationError

from wtforms.fields.html5 import DateField
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


class SearchForm(FlaskForm):
    startDate = DateField("Start Date (YYYY-MM-DD)",id="startDate", validators=[validators.Optional()],render_kw={"class":"datepicker"})
    endDate = DateField("End Date (YYYY-MM-DD)", id="endDate", validators=[validators.Optional()],render_kw={"class":"datepicker"})
    studentId = TextAreaField('Student Id')
    location = TextAreaField('Location')
    email = TextAreaField('Email')
    # download = BooleanField('Download Results')
