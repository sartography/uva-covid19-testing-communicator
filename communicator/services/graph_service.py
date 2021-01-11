import re

from sqlalchemy import func

from communicator import db, app
from communicator.models.sample import Sample
import random
import logging
import datetime as dt
from sqlalchemy import func, and_, case

def dow_count(start, end):
    # Sunday, Monday, ...
    counts = [0 for _ in range(7)]
    curr = start
    while curr <= end:
        counts[(1 + curr.weekday()) % 7] += 1
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

    def apply_filters(self, query, ignore_dates=False):
        for key in self.filters:
            if ignore_dates and "date" in key:
                continue
            query = query.filter(self.filters[key])
        return query

    def get_totals_last_week(self):
        location_stats_data = dict()
        # Count by range
        cases = [func.count(case([(and_(Sample.date >= self.start_date - dt.timedelta(14), Sample.date <= self.end_date - dt.timedelta(14)), 1)])),
                 func.count(case([(and_(Sample.date >= self.start_date - dt.timedelta(
                     7), Sample.date <= self.end_date - dt.timedelta(7)), 1)])),
                 func.count(case([(and_(Sample.date >= self.start_date, Sample.date <= self.end_date), 1)]))]

        q = db.session.query(Sample.location,
                             *cases
                             ).group_by(Sample.location)

        q = self.apply_filters(q, ignore_dates=True)

        for result in q:
            location = result[0]
            if location not in location_stats_data:
                location_stats_data[location] = dict()
            location_stats_data[location]["two_week_ago"] = result[1]
            location_stats_data[location]["one_week_ago"] = result[2]
            location_stats_data[location]["search"] = result[3]
        return location_stats_data

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

        q = self.apply_filters(q)
        for result in q:
            location, station = result[0], result[1]
            if location not in hourly_charts_data:
                hourly_charts_data[location] = dict()
            # Here I'm accounting for the difference in UTC and GMT time zones
            # by moving the five results from the start to the end.
            offset = 6
            counts = result[2:]
            counts = counts[offset:] + counts[:offset]
            hourly_charts_data[location][station] = [
                round(i/days_in_search + .4) for i in counts]
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
        q = self.apply_filters(q)

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
                case([(func.extract('dow', Sample.date) == i, 1)])))

        q = db.session.query(Sample.location, Sample.station,
                             *cases
                             ).group_by(Sample.location, Sample.station)
        q = self.apply_filters(q)

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
        try:
            if "student_id" in filters:
                self.filters["student_id"] = Sample.student_id.in_(
                    filters["student_id"].split())
            if "location" in filters:
                self.filters["location"] = Sample.location.in_(
                    filters["location"].split())
            if "station" in filters:
                self.filters["station"] = Sample.station.in_(
                    filters["station"].split())
            if "compute_id" in filters:
                self.filters["compute_id"] = Sample.computing_id.in_(
                    filters["compute_id"].split())
            if "start_date" in filters:
                self.filters["start_date"] = Sample.date >= filters["start_date"]
                self.start_date = filters["start_date"]
            if "end_date" in filters:
                self.filters["end_date"] = Sample.date <= filters["end_date"]
                self.end_date = filters["end_date"]
            if not "include_tests" in filters:
                self.filters["include_tests"] = Sample.student_id != 0
            else:
                del self.filters["include_tests"]

        except Exception as e:
            logging.error(
                "Encountered an error building filters, so clearing. " + str(e))
