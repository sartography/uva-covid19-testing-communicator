import datetime
from time import sleep

from tests.base_test import BaseTest

import json
from communicator.models import Sample
from communicator import db, app
from communicator.api import admin
from communicator.models.notification import Notification


from communicator.services.graph_service import GraphService, daterange
from datetime import date, timedelta
import json
import random
class TestGraphService(BaseTest):
    def test_populate_db(self):
        samples = db.session.query(Sample).all()
        self.assertEqual(0, len(samples))
        days = 7 * 5
        
        for day in daterange(date.today() - timedelta(days), date.today()):
            day_string = day.strftime("%d-%m-%y")
            bar_code = '000000111-' + day_string + '-5030'
            _sample = Sample(barcode=bar_code,
                    location= 50,
                    station= 20,
                    date=day,
                    created_on=day,
                    last_modified=datetime.datetime.now(),  # Note Modified date is later than created date.
                    student_id="000000111",
                    email="daniel.h.funk@gmail.com",
                    result_code="12345",
                    ivy_file="xxx",
                    email_notified=True,
                    text_notified=True)
            db.session.add(_sample)
        db.session.commit()
        samples = db.session.query(Sample).all()
        self.assertNotEqual(0, len(samples))

    def test_get_totals_by_hour(self):
        self.test_populate_db()
        graph = GraphService() 
        graph.update_search_filters({
            #"start_date": datetime.date(2019,11,1),
            #"end_date": datetime.date(2021,11,1),
        })
        result = graph.get_totals_by_hour()
        self.assertTrue(len(result) > 0)

        self.assertEqual(result[50][20][-6], 36)
        
    def test_get_totals_by_day(self):
        self.test_populate_db()
        graph = GraphService() 
        graph.update_search_filters({
           
        })
        result = graph.get_totals_by_day()
        self.assertTrue(len(result) > 0)
        for location in result:
            for station in result[location]:
                for day in result[location][station]:
                    self.assertEqual(day, 1)

    def test_get_totals_by_weekday(self):
        self.test_populate_db()
        graph = GraphService() 
        graph.update_search_filters({
           
        })
        result = graph.get_totals_by_weekday()
        self.assertTrue(len(result) > 0)
        print(result)
        for location in result:
            for station in result[location]:
                for weekday in result[location][station]:
                    self.assertTrue((weekday == 5 or weekday == 6 ))
