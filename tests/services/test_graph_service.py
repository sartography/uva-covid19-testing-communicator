import datetime
import logging
import pytz

from tests.base_test import BaseTest

from communicator import db, app
from communicator.models import Sample
from communicator.services.graph_service import GraphService, daterange
from datetime import date, timedelta
import json

class TestGraphService(BaseTest):
    def populate_test_db(self):
        days = 50


        for day in daterange(date.today() - timedelta(days), date.today()):
            _sample = Sample(barcode="000000111-202009091449-4321", location = 50, station = 30, student_id = "000000111",
                        computing_id = "abc12d")
            _sample.date = day
            db.session.add(_sample)
        db.session.commit()
        samples = db.session.query(Sample).all()
        self.assertNotEqual(0, len(samples))

    def test_get_totals_last_week(self):
        graph = GraphService() 
        self.populate_test_db()
        graph.update_search_filters({
            "start_date": datetime.date(2020,11,1),
            "end_date": datetime.date(2020,11,1),
        })
        result = graph.get_totals_last_week()
        for location in result:
            for station in location:
                self.assertEqual(result[location][station], 0)

    def test_get_totals_by_hour(self):
        graph = GraphService() 
        self.populate_test_db()
        graph.update_search_filters({
            "start_date": datetime.date(2020,11,1),
            "end_date": datetime.date(2020,11,1),
        })
        result = graph.get_totals_by_hour()
        for location in result:
            for station in location:
                self.assertEqual(result[location][station], 0)
        
    def test_get_totals_by_day(self):
        graph = GraphService() 
        self.populate_test_db()
        graph.update_search_filters({
            "start_date": datetime.date(2020,11,1),
            "end_date": datetime.date(2020,11,1),
        })
        result = graph.get_totals_by_day()
        for location in result:
            for station in location:
                self.assertEqual(result[location][station], 0)

    def test_get_totals_by_weekday(self):
        graph = GraphService() 
        self.populate_test_db()
        graph.update_search_filters({
            "start_date": date.today() - timedelta(100),
            "end_date": date.today(),
            "location": "50"
        })
        result = graph.get_totals_by_weekday()
        print(result)
        self.assertTrue(20 not in result)
        self.assertEqual(result[50][0][1],17)
        self.assertEqual(result[50][10][1],16)
        self.assertEqual(result[50][20][1],14)
        self.assertEqual(result[50][30][1],17)
        self.assertEqual(result[50][40][1],20)
        self.assertEqual(result[50][50][1],14)