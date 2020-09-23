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
