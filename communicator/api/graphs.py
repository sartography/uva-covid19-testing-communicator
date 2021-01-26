import smtplib
from datetime import datetime

from communicator import db, app, executor

from communicator.services.ivy_service import IvyService
from communicator.services.notification_service import NotificationService
from communicator.services.graph_service import GraphService
from time import sleep
import numpy as np
from sqlalchemy import func

from communicator import db
import marshmallow
from flask import jsonify
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from communicator.models.notification import Notification

def parse_form():
    pass

def get_totals_by_day(start_date, end_date, student_id, compute_id, location):
    graph = GraphService()
    filters = dict()
    filters["start_date"] =  datetime.strptime(start_date, "%m/%d/%Y").date()
    filters["end_date"] =  datetime.strptime(end_date, "%m/%d/%Y").date()
    filters["student_id"] = student_id.split() if len(student_id.split()) > 0 else None
    filters["compute_id"] = compute_id.split() if len(compute_id.split()) > 0 else None
    filters["location"] = [int(i) for i in location.split()] if len(location.split()) > 0 else None

    graph.update_search_filters(filters)
    data = graph.get_totals_by_day()
    if (len(data) > 1):
        temp = data
        data = dict()
        for location in temp:
            data[location] = np.sum([temp[location][station] for station in temp[location]],axis=0,dtype=np.int).tolist()       
    elif (len(data) == 1):
        data = data[list(data.keys())[0]]   
    else:
        data = [] 
    return jsonify(data)

def get_totals_by_weekday(start_date, end_date, student_id, compute_id, location):
    graph = GraphService()
    filters = dict()
    filters["start_date"] =  datetime.strptime(start_date, "%m/%d/%Y").date()
    filters["end_date"] =  datetime.strptime(end_date, "%m/%d/%Y").date()
    filters["student_id"] = student_id.split() if len(student_id.split()) > 0 else None
    filters["compute_id"] = compute_id.split() if len(compute_id.split()) > 0 else None
    filters["location"] = [int(i) for i in location.split()] if len(location.split()) > 0 else None

    graph.update_search_filters(filters)
    data = graph.get_totals_by_weekday()

    if (len(data) > 1):
        temp = data
        data = dict()
        for location in temp:
            data[location] = np.sum([temp[location][station] for station in temp[location]],axis=0,dtype=np.int).tolist()       
    elif (len(data) == 1):
        data = data[list(data.keys())[0]]   
    else:
        data = [] 
    return jsonify(data)

def get_totals_by_hour(start_date, end_date, student_id, compute_id, location):
    graph = GraphService()
    filters = dict()
    filters["start_date"] =  datetime.strptime(start_date, "%m/%d/%Y").date()
    filters["end_date"] =  datetime.strptime(end_date, "%m/%d/%Y").date()
    filters["student_id"] = student_id.split() if len(student_id.split()) > 0 else None
    filters["compute_id"] = compute_id.split() if len(compute_id.split()) > 0 else None
    filters["location"] = [int(i) for i in location.split()]  if len(location.split()) > 0 else None

    graph.update_search_filters(filters)
    data = graph.get_totals_by_hour()
    if (len(data) > 1):
        temp = data
        data = dict()
        for location in temp:
            data[location] = np.sum([temp[location][station] for station in temp[location]],axis=0,dtype=np.int).tolist()       
    elif (len(data) == 1):
        data = data[list(data.keys())[0]]   
    else:
        data = [] 
    return jsonify(data)

def get_totals_by_range(start_date, end_date, student_id, compute_id, location):
    pass
    
    # # Aggregate results 
    # for location in location_stats_data:     
    #     
    #     overall_totals_data["one_week_ago"] += location_stats_data[location]["one_week_ago"]
    #     overall_totals_data["two_week_ago"] += location_stats_data[location]["two_week_ago"]
    #     overall_totals_data["search"] += location_stats_data[location]["search"]