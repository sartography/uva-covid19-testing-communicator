import smtplib
from datetime import datetime

from communicator import db, app, executor
from communicator.services.graph_service import GraphService

import numpy as np

import marshmallow
from flask import jsonify
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from communicator.models.notification import Notification

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

def get_totals_by_day(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = ""):
  
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
    graph = GraphService()
    
    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_day())
    
def get_totals_by_weekday(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = ""):

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
    
    graph = GraphService()
   
    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_weekday())
    
def get_totals_by_hour(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = ""):
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
    graph = GraphService()

    graph.update_search_filters(filters)
    return form_graph_response(graph.get_totals_by_hour())
    
def get_totals_by_range(last_modified = None, start_date = None, end_date = None, student_id = "", compute_id = "", location = ""):
    pass
    
    # # Aggregate results 
    # for location in location_stats_data:     
    #     
    #     overall_totals_data["one_week_ago"] += location_stats_data[location]["one_week_ago"]
    #     overall_totals_data["two_week_ago"] += location_stats_data[location]["two_week_ago"]
    #     overall_totals_data["search"] += location_stats_data[location]["search"]