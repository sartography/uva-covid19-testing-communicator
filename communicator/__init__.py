
import random
import csv
import io
import json

import logging
import os
from datetime import datetime
from datetime import date
from functools import wraps

import connexion
import sentry_sdk
from connexion import ProblemException
from flask import render_template, request, redirect, url_for, flash, abort, Response, send_file, session
from flask_assets import Environment
from flask_cors import CORS
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_paginate import Pagination, get_page_parameter
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, case
from sentry_sdk.integrations.flask import FlaskIntegration
from webassets import Bundle
from flask_executor import Executor

import numpy as np
logging.basicConfig(level=logging.INFO)

# API, fully defined in api.yml
connexion_app = connexion.FlaskApp(__name__)
app = connexion_app.app

# Executor for long running tasks
executor = Executor(app)


# Configuration
app.config.from_object('config.default')
if "TESTING" in os.environ and os.environ["TESTING"] == "true":
    app.config.from_object('config.testing')
    app.config.from_pyfile('../config/testing.py')
else:
    app.config.root_path = app.instance_path
    app.config.from_pyfile('config.py', silent=True)


# Connexion Error handling
def render_errors(exception):
    return Response(json.dumps({"error": str(exception)}), status=500, mimetype="application/json")


connexion_app.add_error_handler(Exception, render_errors)


# Mail settings
mail = Mail(app)

# Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)

# Asset management
url_map = app.url_map
try:
    for rule in url_map.iter_rules('static'):
        url_map._rules.remove(rule)
except ValueError:
    # no static view was created yet
    pass
app.add_url_rule(
    app.static_url_path + '/<path:filename>',
    endpoint='static', view_func=app.send_static_file)
assets = Environment(app)
assets.init_app(app)
assets.url = app.static_url_path
scss = Bundle(
    'assets/scss/argon.scss',
    filters='pyscss',
    output='argon.css'
)
assets.register('app_scss', scss)

connexion_app.add_api('api.yml', base_path='/v1.0')

from datetime import date, timedelta
from communicator import models
from communicator import api
from communicator import forms
from communicator.models import Sample
from flask_table import Table, Col, DatetimeCol, BoolCol, NestedTableCol
from communicator.tables import SampleTable
# Convert list of allowed origins to list of regexes
origins_re = [r"^https?:\/\/%s(.*)" % o.replace('.', r'\.')
              for o in app.config['CORS_ALLOW_ORIGINS']]
cors = CORS(connexion_app.app, origins=origins_re)

# Sentry error handling
if app.config['ENABLE_SENTRY']:
    sentry_sdk.init(
        dsn="https://048a9b3ac72f476a8c77b910ad4d7f84@o401361.ingest.sentry.io/5454621",
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

# HTML Pages
BASE_HREF = app.config['APPLICATION_ROOT'].strip('/')


def superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from communicator.services.user_service import UserService
        if not UserService().is_valid_user():
            flash("You do not have permission to view that page", "warning")
            logging.info("Permission Denied to user " +
                         UserService().get_user_info())
            abort(404)
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(404)
@superuser
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('pages/404.html')

def daterange(start, stop, days = 1, hours =  0):
    if (type(start) == date):
        start = date2datetime(start)
    if (type(stop) == date):
        stop = date2datetime(stop)
    time = start
    date_list = []
    while time <= stop:
        date_list.append(time)
        time += timedelta(days=days,hours=hours)
    return date_list
    
def date2datetime(_date):
    return datetime.combine(_date, datetime.min.time())

def apply_filters(query, session):
    if "index_filter" in session:
        filters = session["index_filter"]
        try:
            if "start_date" in filters:
                query = query.filter(
                    Sample.date >= filters["start_date"])
            else:
                filters["start_date"] = date.today()
                query = query.filter(
                    Sample.date >= filters["start_date"])
            if "end_date" in filters:
                query = query.filter(
                    Sample.date <= filters["end_date"])
            else:
                filters["end_date"] = date.today() + timedelta(1)
            if "student_id" in filters:
                query = query.filter(
                    Sample.student_id.in_(filters["student_id"].split()))
            if "location" in filters:
                query = query.filter(
                    Sample.location.in_(filters["location"].split()))
            if "station" in filters:
                query = query.filter(
                    Sample.station.in_(filters["station"].split()))
            if "compute_id" in filters:
                filtered_samples = filtered_samples.filter(
                    Sample.compute_id.in_(filters["compute_id"].split()))
        except Exception as e:
            logging.error(
                "Encountered an error building filters, so clearing. " + str(e))
            session["index_filter"] = {}
    else:
        # Default to Todays Results
        filters = dict()
        filters["start_date"] = date.today()
        filters["end_date"] = date.today() + timedelta(1)
        query = query.filter(
            Sample.date >= filters["start_date"])
    if type(filters["start_date"]) == str:
        filters["start_date"] = datetime.strptime(filters["start_date"].strip(), "%Y-%m-%d").date()
    if type(filters["end_date"]) == str:
        filters["end_date"] = datetime.strptime(filters["end_date"].strip(), "%Y-%m-%d").date()

    return query, filters

def ingest_form(form):
    pass
def group_columns(data):
    grouped_data = []
    for entry in data:
        grouped_data.append({"barcode":entry.barcode,
                             "date":entry.date,
                             "notifications":entry.notifications,

                             "ids":[dict(type = "computing_id",
                                         data = entry.computing_id),
                                    dict(type = "student_id",
                                         data = entry.student_id)],
                             "contacts":[dict(type="phone",
                                              data=entry.phone),
                                         dict(type="email",
                                              data=entry.email)],
                             "taken_at":[dict(type="location",
                                              data=entry.location),
                                         dict(type="station",
                                              data=entry.station)],
                             }
                             )
    return grouped_data

@app.route('/', methods=['GET', 'POST'])
@superuser
def index():

    form = forms.SearchForm(request.form)
    action = BASE_HREF + "/"
    
    if request.method == "POST" or request.args.get('cancel') == 'true':
        session["index_filter"] = {}  # Clear out the session if it is invalid.
    
    if form.validate():
        session["index_filter"] = {}
        if form.dateRange.data:
            start, end = form.dateRange.data.split("-")
            session["index_filter"]["start_date"] = datetime.strptime(start.strip(), "%m/%d/%Y").date()
            session["index_filter"]["end_date"] =  datetime.strptime(end.strip(), "%m/%d/%Y").date() + timedelta(1)
        if form.studentId.data:
            session["index_filter"]["student_id"] = form.studentId.data
        if form.location.data:
            session["index_filter"]["location"] = form.location.data
        if form.compute_id.data:
            session["index_filter"]["compute_id"] = form.compute_id.data
    samples = db.session.query(Sample).order_by(Sample.date.desc())
    # Store previous form submission settings in the session, so they are preseved through pagination.
    filtered_samples, filters = apply_filters(samples, session)

    if request.args.get('download') == 'true':
        csv = __make_csv(filtered_samples)
        return send_file(csv, attachment_filename='data_export.csv', as_attachment=True)
    
    location_charts_data = {}
    hourly_chart_data = {}
    weekday_chart_data = {}
    overall_chart_data = {}

    important_dates = {}
    overall_stat_data = {
                    "one_week_ago":0,
                    "two_week_ago":0,
                    "today":0,
                }
    location_stats_data = {}
    
    today = filters["end_date"] - timedelta(1)
    days_in_search = (filters["end_date"] - filters["start_date"]).days
    one_week_ago = filters["end_date"] - timedelta(7)
    two_weeks_ago = one_week_ago - timedelta(7)
    chart_ticks = [] 
    
    if days_in_search <= 1: 
        timeFormat = "%I:%M %p"
        hours = 2
        days = 0
    elif days_in_search <= 3:
        timeFormat = "%m/%d %I %p"
        hours = 4
        days = 0
    else:
        timeFormat = "%m/%d"
        hours = 0
        days = 1
    
    # Count by Day
    bounds = daterange(filters["start_date"], filters["end_date"], days=days, hours=hours)
    chart_ticks = []
    for i in range(len(bounds) - 1):
        chart_ticks.append(f"{bounds[i].strftime(timeFormat)} - {bounds[i+1].strftime(timeFormat)}")

    cases = [ ]  
    for i in range(len(bounds) - 1):
        cases.append(func.count(case([(and_(Sample.date >= bounds[i], Sample.date <= bounds[i+1]), 1)])))
    
    q = db.session.query(Sample.location, Sample.station,
        *cases\
        ).group_by(Sample.location, Sample.station)

    q, filters = apply_filters(q , session)

    for result in q:
        location, station = result[0], result[1]
        if location not in location_charts_data: location_charts_data[location] = dict()
        location_charts_data[location][station] = result[2:]

    # Count by hour
    cases = [ ]  
    for i in range(24):
        cases.append(func.count(case([(func.extract('hour', Sample.date) == i, 1)])))
    
    q = db.session.query(Sample.location, Sample.station,
        *cases\
        ).group_by(Sample.location, Sample.station)

    q, filters = apply_filters(q, session)

    for result in q:
        location = result[0]
        hourly_chart_data[location] = result[1:]
    
    # Count by weekday
    cases = [ ]  
    for i in range(7):
        cases.append(func.count(case([(func.extract('dow', Sample.date) == i, 1)])))
    
    q = db.session.query(Sample.location,
        *cases\
        ).group_by(Sample.location)

    q, filters = apply_filters(q , session)

    for result in q:
        location = result[0]
        weekday_chart_data[location] = [i/days_in_search for i in result[1:]]
    # Count by range
    cases = [func.count(case([(and_(Sample.date >= two_weeks_ago, Sample.date <= filters["end_date"]), 1)])),
            func.count(case([(and_(Sample.date >= one_week_ago, Sample.date <= filters["end_date"]), 1)])),
            func.count(case([(and_(Sample.date >= today, Sample.date <= filters["end_date"]), 1)]))]  
    
    q = db.session.query(Sample.location,
        *cases\
        ).group_by(Sample.location)

    q, filters = apply_filters(q , session)

    for result in q:
        location = result[0]
        if location not in location_stats_data: location_stats_data[location] = dict()
        location_stats_data[location]["two_week_ago"] = result[1]
        location_stats_data[location]["one_week_ago"] = result[2]
        location_stats_data[location]["today"] = result[3]

    # Aggregate results 
    for location in location_stats_data:     
        overall_chart_data[location] = np.sum([location_charts_data[location][station] for station in location_charts_data[location]],axis=0).tolist()
    
        overall_stat_data["one_week_ago"] += location_stats_data[location]["one_week_ago"]
        overall_stat_data["two_week_ago"] += location_stats_data[location]["two_week_ago"]
        overall_stat_data["today"] += location_stats_data[location]["today"]

    important_dates = {
        "today" : (filters["end_date"] - timedelta(1)).strftime("%m/%d/%Y"),
        "range" : filters["start_date"].strftime("%m/%d/%Y") + " - " + (filters["end_date"] - timedelta(1)).strftime("%m/%d/%Y"),
        "one_week_ago" : one_week_ago.strftime("%m/%d/%Y"),
        "two_weeks_ago" : two_weeks_ago.strftime("%m/%d/%Y"),
        }
    ################# Raw Samples Table ##############
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=filtered_samples.count(
    ), search=False, record_name='samples', css_framework='bootstrap4')
    
    table = SampleTable(group_columns(filtered_samples[page * 10:(page * 10) + 10]))
    

    return render_template('layouts/default.html',
                           base_href=BASE_HREF,
                           content=render_template(
                               'pages/index.html',
                               form = form,
                               dates = important_dates,
                               table = table,
                               action = action,
                               pagination = pagination,

                               chart_ticks = chart_ticks,
                               overall_chart_data = overall_chart_data,
                               location_charts_data = location_charts_data,
                               hourly_chart_data = hourly_chart_data,
                               weekday_chart_data = weekday_chart_data,

                               overall_stat_data = overall_stat_data,
                               location_stats_data = location_stats_data,
                           ))

@app.route('/activate', methods=['GET', 'POST'])
@superuser
def activate_station():
    return render_template('layouts/default.html',
                           base_href=BASE_HREF,
                           content=render_template(
                               'pages/stations.html'))


def __make_csv(sample_query):
    csvfile = io.StringIO()
    headers = [
        'barcode',
        'student_id',
        'date',
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
                'date': sample.date,
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


@app.route('/invitation', methods=['GET', 'POST'])
@superuser
def send_invitation():
    from communicator.models.invitation import Invitation
    from communicator.tables import InvitationTable

    form = forms.InvitationForm(request.form)
    action = BASE_HREF + "/invitation"
    title = "Send invitation to students"
    if request.method == 'POST' and form.validate():
        from communicator.services.notification_service import NotificationService
        with NotificationService(app) as ns:
            ns.send_invitations(
                form.date.data, form.location.data, form.emails.data)
            return redirect(url_for('send_invitation'))
    # display results
    page = request.args.get(get_page_parameter(), type=int, default=1)
    invites = db.session.query(Invitation).order_by(
        Invitation.date_sent.desc())
    pagination = Pagination(page=page, total=invites.count(),
                            search=False, record_name='samples')

    table = InvitationTable(invites.paginate(page, 10, error_out=False).items)

    return render_template(
        'form.html',
        form=form,
        table=table,
        pagination=pagination,
        action=action,
        title=title,
        description_map={},
        base_href=BASE_HREF
    )


@app.route('/imported_files', methods=['GET'])
@superuser
def list_imported_files_from_ivy():
    from communicator.models.ivy_file import IvyFile
    from communicator.tables import IvyFileTable

    # display results
    page = request.args.get(get_page_parameter(), type=int, default=1)
    files = db.session.query(IvyFile).order_by(IvyFile.date_added.desc())
    pagination = Pagination(page=page, total=files.count(),
                            search=False, record_name='samples')

    table = IvyFileTable(files.paginate(page, 10, error_out=False).items)
    return render_template(
        'imported_files.html',
        table=table,
        pagination=pagination,
        base_href=BASE_HREF
    )


@app.route('/sso')
def sso():
    from communicator.services.user_service import UserService
    user = UserService().get_user_info()
    response = ""
    response += f"<h1>Current User: {user.display_name} ({user.uid})</h1>"
    return response


@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0


# Access tokens
@app.cli.command()
def globus_token():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    ivy_service.get_access_token()


@app.cli.command()
def count_files_in_ivy():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    count = ivy_service.get_file_count_from_globus()
    print(f"There are {count} files awaiting transfer")


@app.cli.command()
def transfer():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    ivy_service.request_transfer()


@app.cli.command()
def delete():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    ivy_service.delete_file()
