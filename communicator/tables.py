from babel.dates import format_datetime, get_timezone
from flask_table import Table, Col, DatetimeCol, BoolCol, NestedTableCol


class BetterDatetimeCol(Col):
    """Format the content as a datetime, unless it is None, in which case,
    output empty.

    """
    def __init__(self, name, datetime_format='short', tzinfo='', locale='', **kwargs):
        super(BetterDatetimeCol, self).__init__(name, **kwargs)
        self.datetime_format = datetime_format
        self.tzinfo = tzinfo
        self.locale = locale

    def td_format(self, content):
        if content:
            return format_datetime(content, self.datetime_format, self.tzinfo, self.locale)
        else:
            return ''


class NotificationTAale(Table):
    type = Col('type')
    date = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    successful = BoolCol('Success?')
    error_message = Col('error')


class SampleTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    barcode = Col('Barcode')
    student_id = Col('Student Id')
    date = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    location = Col('Location')
    phone = Col('Phone')
    email = Col('Email')
    notifications = NestedTableCol('notifications', NotificationTAale)


class IvyFileTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    file_name = Col('File Name')
    date_added = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    sample_count = Col('Total Records')


class InvitationTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    date_sent = BetterDatetimeCol('Date Sent', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    location = Col('Location')
    date = Col('Date')
    total_recipients = Col('# Recipients')
