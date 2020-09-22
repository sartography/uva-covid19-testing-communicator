from flask_table import Table, Col, LinkCol, BoolCol, DatetimeCol, NestedTableCol
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, BooleanField, SelectField, validators, HiddenField, TextAreaField
from wtforms.widgets import TextArea


class InvitationForm(FlaskForm):
    location = StringField('Location (ex. Newcomb Hall, South Meeting Room)', [validators.DataRequired()])
    date = StringField('Date (ex. Monday, September 23 from 10:00 am-5:00 pm ', [validators.DataRequired()])
    emails = TextAreaField('Emails (newline delimited)', render_kw={'rows': 50, 'cols': 50})
