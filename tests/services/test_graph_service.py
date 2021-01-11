import datetime

import pytz

from tests.base_test import BaseTest


from communicator import app
from communicator.models import Sample
from communicator.services.graph_service import GraphService


class TestGraphService(BaseTest):

    def test_get_totals_last_week(self):
        graph = GraphService() 
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
        graph.update_search_filters({
            "start_date": datetime.date(2020,11,1),
            "end_date": datetime.date(2020,11,14),
            "location": "50"
        })
        result = graph.get_totals_by_weekday()
        self.assertEqual(result[50][00][1],17)
        self.assertEqual(result[50][10][1],16)
        self.assertEqual(result[50][20][1],14)
        self.assertEqual(result[50][30][1],17)
        self.assertEqual(result[50][40][1],20)
        self.assertEqual(result[50][50][1],14)