import re

from sqlalchemy import func

from communicator import db, app
from communicator.models.sample import Sample
import random
import logging
import datetime as dt
from sqlalchemy import func, and_, case, or_
from communicator.api.admin import add_sample_search_filters

def dow_count(start, end):
    # Sunday, Monday, ...
    counts = [0 for _ in range(7)]
    curr = start
    while curr <= end:
        counts[curr.weekday()] += 1
        curr += dt.timedelta(1)
    return counts


def date2datetime(_date):
    return dt.datetime.combine(_date, dt.datetime.min.time())


def daterange(start, stop, days=1, hours=0):
    if (type(start) == dt.date):
        start = date2datetime(start)
    if (type(stop) == dt.date):
        stop = date2datetime(stop)
    time = start
    date_list = []
    while time <= stop:
        date_list.append(time)
        time += dt.timedelta(days=days, hours=hours)
    return date_list


class GraphService(object):
    def __init__(self):
        self.filters = dict()
        self.filters["start_date"] = Sample.date >= dt.date.today()
        self.start_date = dt.date.today()
        self.filters["end_date"] = Sample.date <= dt.date.today() + \
            dt.timedelta(1)
        self.end_date = dt.date.today() + dt.timedelta(1)

    def get_totals_by_hour(self):
        hourly_charts_data = dict()
        days_in_search = (self.end_date - self.start_date).days

        cases = []
        for i in range(24):
            cases.append(func.count(
                case([(func.extract('hour', Sample.date) == i, 1)])))

        q = db.session.query(Sample.location, Sample.station,
                             *cases
                             ).group_by(Sample.location, Sample.station)

        q = add_sample_search_filters(q, self.filters)
        for result in q:
            location, station = result[0], result[1]
            if location not in hourly_charts_data:
                hourly_charts_data[location] = dict()
            # Here I'm accounting for the difference in UTC and GMT time zones
            # by moving the five results from the start to the end.
            offset = 6
            counts = result[2:]
            counts = counts[offset:] + counts[:offset]
            hourly_charts_data[location][station] = [round(i/days_in_search + .4) for i in counts]
        return hourly_charts_data

    def get_totals_by_day(self):
        daily_charts_data = dict()
        bounds = daterange(self.start_date, self.end_date, days=1, hours=0)
        cases = []
        for i in range(len(bounds) - 1):
            cases.append(func.count(
                case([(and_(Sample.date >= bounds[i], Sample.date <= bounds[i+1]), 1)])))

        q = db.session.query(Sample.location, Sample.station,
                             *cases
                             ).group_by(Sample.location, Sample.station)
        
        q = add_sample_search_filters(q, self.filters)

        for result in q:
            location, station = result[0], result[1]
            if location not in daily_charts_data:
                daily_charts_data[location] = dict()
            daily_charts_data[location][station] = result[2:]

        return daily_charts_data

    def get_totals_by_weekday(self):
        weekday_charts_data = dict()
        dow_counts = dow_count(
            self.start_date, self.end_date - dt.timedelta(1))
        cases = []
        for i in range(7):
            cases.append(func.count(
                case([(func.extract('isodow', Sample.date) == i + 1, 1)])))

        q = db.session.query(Sample.location, Sample.station,
                             *cases
                             ).group_by(Sample.location, Sample.station)
        q = add_sample_search_filters(q, self.filters)
        for result in q:
            location, station = result[0], result[1]
            if location not in weekday_charts_data:
                weekday_charts_data[location] = dict()
            weekday_charts_data[location][station] = []
            for dow, total in zip(range(7), result[2:]):
                if dow_counts[dow] > 0:
                    weekday_charts_data[location][station].append(
                        round(total/dow_counts[dow] + .4))
                else:
                    weekday_charts_data[location][station].append(total)
        return weekday_charts_data

    def update_search_filters(self, filters):
        self.filters = filters
        if "start_date" in filters:
            self.start_date = filters["start_date"]
        if "end_date" in filters:
            self.end_date = filters["end_date"] + dt.timedelta(1)

 