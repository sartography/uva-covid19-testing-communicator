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

class InventoryDepositTable(Table):
    classes = ["table","align-items-center","table-flush"]
    date_added = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    amount = Col('Amount')

class NotificationTable(Table):
    type = Col('type')
    date = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    successful = BoolCol('Success?')
    error_message = Col('error')

class NestedDataColumn(Table):
    type = Col('Type')
    data = Col('Data')

class SampleTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    classes = ["table","align-items-center","table-flush"]
    barcode = Col('Barcode')
    date = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    # station = Col('Station')  # TODO: Pad with leading 0s to 4 digits
    ids = NestedTableCol('IDs', NestedDataColumn)
    taken_at = NestedTableCol('Taken at', NestedDataColumn)  # TODO: Pad with leading 0s to 4 digits
    contacts = NestedTableCol('contacts', NestedDataColumn)
    notifications = NestedTableCol('notifications', NotificationTable)

class IvyFileTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    classes = ["table","align-items-center","table-flush"]
    file_name = Col('File Name')
    date_added = BetterDatetimeCol('Date', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    sample_count = Col('Total Records')


class InvitationTable(Table):
    classes = ["table","align-items-center","table-flush"]
    def sort_url(self, col_id, reverse=False):
        pass
    date_sent = BetterDatetimeCol('Date Sent', "medium", tzinfo=get_timezone('US/Eastern'), locale='en')
    location = Col('Location')
    date = Col('Date')
    total_recipients = Col('# Recipients')