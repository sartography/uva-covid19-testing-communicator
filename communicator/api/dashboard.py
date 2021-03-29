import csv
import io
from datetime import datetime
from datetime import timedelta

import numpy as np
from babel.dates import format_datetime, get_timezone
from flask import jsonify, send_file
from sqlalchemy import func, case, and_

from communicator import db
from communicator.api.admin import add_sample_search_filters
from communicator.models import Deposit
from communicator.models import SampleSchema, Sample
from communicator.models.notification import Notification
from communicator.services.graph_service import GraphService


def form_graph_response(data):
    locations = list(data.keys())
    if (len(locations) > 1):
        temp = data
        data = dict()
        for location in temp:
            data[location] = np.sum([temp[location][station] for station in temp[location]],axis=0,dtype=np.int).tolist()       
    elif (len(locations) == 1):
        data = data[locations[0]]
    return jsonify(data)

def get_totals_by_day(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = "", include_tests=""):
  
    filters = dict()
    if start_date != None:
        filters["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").date()
    if end_date != None:
        filters["end_date"] = datetime.strptime(end_date, "%m/%d/%Y").date()
    if len(student_id.strip()) > 0:
        filters["student_id"] = student_id.split()
    if len(compute_id.strip()) > 0:
        filters["compute_id"] = compute_id.split() 
    if len(location.strip()) > 0:
        filters["location"] = [int(i) for i in location.split()]
    if include_tests == "true":
        filters["include_tests"] = include_tests
    graph = GraphService()
    
    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_day())
    
def get_totals_by_weekday(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = "", include_tests =""):

    filters = dict()
    if start_date != None:
        filters["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").date()
    if end_date != None:
        filters["end_date"] = datetime.strptime(end_date, "%m/%d/%Y").date()
    if len(student_id) > 0:
        filters["student_id"] = student_id.split()
    if len(compute_id) > 0:
        filters["compute_id"] = compute_id.split() 
    if len(location) > 0:
        filters["location"] = [int(i) for i in location.split()]
    if include_tests == "true":
        filters["include_tests"] = include_tests    
    graph = GraphService()
   
    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_weekday())
    
def get_totals_by_hour(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = "",include_tests="") :
    filters = dict()
    if start_date != None:
        filters["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").date()
    if end_date != None:
        filters["end_date"] = datetime.strptime(end_date, "%m/%d/%Y").date()
    if len(student_id) > 0:
        filters["student_id"] = student_id.split()
    if len(compute_id) > 0:
        filters["compute_id"] = compute_id.split() 
    if len(location) > 0:
        filters["location"] = [int(i) for i in location.split()]
    if include_tests == "true":
        filters["include_tests"] = include_tests
    graph = GraphService()

    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_hour())


def __get_samples_query(last_modified = None, start_date = None, end_date = None,
                        student_id = "", compute_id = "", location = "", include_tests= "", page = 0):
    query = db.session.query(Sample)
    filters = dict()
    if start_date != None:
        filters["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").date()
    if end_date != None:
        filters["end_date"] = datetime.strptime(end_date, "%m/%d/%Y").date()
    if len(student_id.strip()) > 0:
        filters["student_id"] = student_id.split()
    if len(compute_id.strip()) > 0:
        filters["compute_id"] = compute_id.split()
    if len(location.strip()) > 0:
        filters["location"] = [int(i) for i in location.split()]
    if include_tests == "true":
        filters["include_tests"] = include_tests


    query = add_sample_search_filters(query, filters)
    if last_modified:
        lm_date = datetime.fromisoformat(last_modified)
        query = query.filter(Sample.last_modified > lm_date)

    query = query.order_by(Sample.last_modified)
    return query


def get_samples(last_modified = None, start_date = None, end_date = None,
                student_id = "", compute_id = "", location = "", include_tests= "", page = 0):

    query = __get_samples_query(last_modified, start_date, end_date, student_id, compute_id,
                                location, include_tests)
    samples = query[int(page) * 10:(int(page) * 10) + 10]
    response = SampleSchema(many=True).dump(samples)
    return response


def download_search(last_modified = None, start_date = None, end_date = None,
                   student_id = "", compute_id = "", location = "", include_tests= "", page = 0):

    query = __get_samples_query(last_modified, start_date, end_date, student_id, compute_id,
                                location, include_tests)
    csv = __make_csv(query)
    return send_file(csv, attachment_filename='data_export.csv',
                     mimetype="text/csv",
                     cache_timeout=-1,
                     as_attachment=True)


def __make_csv(sample_query):
    csvfile = io.StringIO()
    headers = [
        'barcode',
        'student_id',
        'date',
        'time',
        'location',
        'phone',
        'email',
        'result_code',
        'ivy_file',
        'email_notified',
        'text_notified'
    ]
    writer = csv.DictWriter(csvfile, headers)
    writer.writeheader()
    for sample in sample_query.all():
        writer.writerow(
            {
                'barcode': sample.barcode,
                'student_id': sample.student_id,
                'date':  format_datetime(sample.date, 'YYYY-MM-dd hh:mm:ss a', get_timezone('US/Eastern'), 'en'),
                'location': sample.location,
                'phone': sample.phone,
                'email': sample.email,
                'result_code': sample.result_code,
                'ivy_file': sample.ivy_file,
                'email_notified': sample.email_notified,
                'text_notified': sample.text_notified,
            }
        )

    # Creating the byteIO object from the StringIO Object
    mem = io.BytesIO()
    mem.write(csvfile.getvalue().encode('utf-8'))
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)
    csvfile.close()
    return mem

    
def get_topbar_data(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = "", include_tests = ""):        
    filters = dict()
    if start_date != None:
        filters["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").date()
    if end_date != None:
        filters["end_date"] = datetime.strptime(end_date, "%m/%d/%Y").date() + timedelta(1)
    if len(student_id.strip()) > 0:
        filters["student_id"] = student_id.split()
    if len(compute_id.strip()) > 0:
        filters["compute_id"] = compute_id.split() 
    if len(location.strip()) > 0:
        filters["location"] = [int(i) for i in location.split()]
    if include_tests == "true":
        filters["include_tests"] = include_tests   
    cases = [func.count(case([(and_(Sample.date >= filters["start_date"], Sample.date <= filters["end_date"]), 1)])),
             func.count(case([(and_(Sample.date >= filters["start_date"] - timedelta(7), Sample.date <= filters["end_date"] - timedelta(7)), 1)])),
             func.count(case([(and_(Sample.date >= filters["start_date"] - timedelta(14), Sample.date <= filters["end_date"] - timedelta(14)), 1)]))]
    
    query = db.session.query(Sample.location,
                             *cases).group_by(Sample.location)
    query = add_sample_search_filters(query, filters, ignore_dates=True)
    
    response = [0,0,0,0,0,0,0,0]
    for result in query: # Add up totats 
        response[0] += result[1]
        response[1] += result[2]
        response[2] += result[3]
    notifications = db.session.query(Notification).filter(Notification.date >= filters["start_date"]).filter(Notification.date <= filters["end_date"])
    response[3] = notifications.filter(Notification.successful == "t").filter(Notification.type == "email").count()
    response[4] = notifications.filter(Notification.successful == "f").filter(Notification.type == "email").count()
    response[5] = notifications.filter(Notification.successful == "t").filter(Notification.type == "text").count()
    response[6] = notifications.filter(Notification.successful == "f").filter(Notification.type == "text").count()
    
    deposits = db.session.query(Deposit).order_by(Deposit.date_added.desc())
    total_deposits = sum([i.amount for i in deposits])
    if deposits.count() > 0:
        sample_count = db.session.query(Sample).filter(Sample.date >= filters["start_date"]).count()
    else:
        sample_count = 0
    response[7] = total_deposits - sample_count
    return response



