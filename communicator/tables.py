from flask_table import Table, Col, DatetimeCol, BoolCol


class SampleTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    barcode = Col('Barcode')
    student_id = Col('Student Id')
    date = DatetimeCol('Date', "medium")
    location = Col('Location')
    email_notified = BoolCol('Emailed?')
    text_notified = BoolCol('Texted?')


class IvyFileTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    file_name = Col('File Name')
    date_added = DatetimeCol('Date', "medium")
    sample_count = Col('Total Records')


class InvitationTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass
    date_sent = DatetimeCol('Date Sent', "medium")
    location = Col('Location')
    date = Col('Date')
    total_recipients = Col('# Recipients')
