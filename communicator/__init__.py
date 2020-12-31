
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
from sqlalchemy import func
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
# Convert list of allowed origins to list of regexes
origins_re = [r"^https?:\/\/%s(.*)" % o.replace('.', '\.')
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

def make_sample_histogram(samples, _range=None):
    if _range == None:
        start = None
        end = None
        _range = (start,end)
    days_in_search = (_range[0] - _range[1]).days
    
    days = 0
    hours = 6 
    bounds = daterange(_range[0], _range[1], days=days, hours=hours)
    counts = [0 for i in range(len(bounds))]
    for entry in samples:
        for i in range(len(bounds) - 1):
            if entry.date > bounds[i] and entry.date < bounds[i+1]:
                counts[i] += 1
                break
    return bounds, counts

@app.route('/', methods=['GET', 'POST'])
@superuser
def index():
    from communicator.models import Sample
    from communicator.tables import SampleTable

    form = forms.SearchForm(request.form)
    action = BASE_HREF + "/"
    samples = db.session.query(Sample).order_by(Sample.date.desc())

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

    # Store previous form submission settings in the session, so they are preseved through pagination.
    filtered_samples = samples
    if "index_filter" in session:
        filters = session["index_filter"]
        try:
            if "start_date" in filters:
                filtered_samples = filtered_samples.filter(
                    Sample.date >= filters["start_date"])
            else:
                filters["start_date"] = date.today()
                filtered_samples = filtered_samples.filter(
                    Sample.date >= filters["start_date"])
            if "end_date" in filters:
                filtered_samples = filtered_samples.filter(
                    Sample.date <= filters["end_date"])
            else:
                filters["end_date"] = date.today() + timedelta(1)
            if "student_id" in filters:
                filtered_samples = filtered_samples.filter(
                    Sample.student_id.in_(filters["student_id"].split()))
            if "location" in filters:
                filtered_samples = filtered_samples.filter(
                    Sample.location.in_(filters["location"].split()))
            if "station" in filters:
                filtered_samples = filtered_samples.filter(
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
        filtered_samples = filtered_samples.filter(
            Sample.date >= filters["start_date"])

    if type(filters["start_date"]) == str:
        filters["start_date"] = datetime.strptime(filters["start_date"].strip(), "%Y-%m-%d").date()
    if type(filters["end_date"]) == str:
        filters["end_date"] = datetime.strptime(filters["end_date"].strip(), "%Y-%m-%d").date()

    if request.args.get('download') == 'true':
        csv = __make_csv(filtered_samples)
        return send_file(csv, attachment_filename='data_export.csv', as_attachment=True)
    
    weekday_totals = [0 for _ in range(7)]  # Mon, Tues, ...
    hour_totals = [0 for _ in range(24)]  # 12AM, 1AM, ...
    
    location_charts_data = {}
    overall_chart_data = {}
    dates = {}
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
    
    if filtered_samples.count() > 0:
        if days_in_search <= 2: 
            bins = 9 * days_in_search
            timeFormat = "%b %e, %I:%M %p"
        else:
            bins =  days_in_search * 3
            timeFormat = "%m/%d/%Y"
        bounds = []

        for entry in filtered_samples:
            if entry.location not in location_charts_data:
                location_charts_data[entry.location] = dict()
                location_stats_data[entry.location] = { "one_week_ago" : 0,
                                                        "two_week_ago" : 0,
                                                        "today" : 0 }

            if entry.station not in location_charts_data[entry.location]:
                samples_at_station = filtered_samples\
                            .filter(Sample.location == entry.location)\
                            .filter(Sample.station == entry.station)

                bounds, counts = make_sample_histogram(samples_at_station, (filters["start_date"],filters["end_date"]))
                location_charts_data[entry.location][entry.station] = counts
                
            weekday_totals[entry.date.weekday()] += 1
            hour_totals[entry.date.hour] += 1

            if entry.date.date() >= two_weeks_ago:
                location_stats_data[entry.location]["two_week_ago"] += 1
                if entry.date.date() >= one_week_ago:
                    location_stats_data[entry.location]["one_week_ago"] += 1
                    if entry.date.date() >= today:
                        location_stats_data[entry.location]["today"] += 1
        chart_ticks = []
        for i in range(len(bounds) - 1):
            chart_ticks.append(f"{bounds[i].strftime(timeFormat)} - {bounds[i+1].strftime(timeFormat)}")

        for location in location_charts_data:            
            overall_stat_data["one_week_ago"] += location_stats_data[entry.location]["one_week_ago"]
            overall_stat_data["two_week_ago"] += location_stats_data[entry.location]["two_week_ago"]
            overall_stat_data["today"] += location_stats_data[entry.location]["today"]

            overall_chart_data[location] = np.sum([location_charts_data[location][station] for station in location_charts_data[location]],axis=0).tolist()
        
        dates = {
        "today" : filters["end_date"].strftime("%m/%d/%Y"),
        "range" : filters["start_date"].strftime("%m/%d/%Y") + " - " + (filters["end_date"] - timedelta(1)).strftime("%m/%d/%Y"),
        "one_week_ago" : one_week_ago.strftime("%m/%d/%Y"),
        "two_weeks_ago" : two_weeks_ago.strftime("%m/%d/%Y"),
        }
    ################# Raw Samples Table ##############
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=filtered_samples.count(
    ), search=False, record_name='samples', css_framework='bootstrap4')

    table = SampleTable(filtered_samples.paginate(
        page, 10, error_out=False).items)

    return render_template('layouts/default.html',
                           base_href=BASE_HREF,
                           content=render_template(
                               'pages/index.html',
                               form = form,
                               dates = dates,
                               table = table,
                               action = action,
                               pagination = pagination,

                               chart_ticks = chart_ticks,
                               overall_chart_data = overall_chart_data,
                               location_charts_data = location_charts_data,

                               overall_stat_data = overall_stat_data,
                               location_stats_data = location_stats_data,

                               weekday_totals = weekday_totals,
                               hour_totals = hour_totals,
                           ))

 
    # # Check for Unresponsive
    # for loc_code in active_stations:
    #     if loc_code not in location_data:
    #         location_dict["datasets"].append({
    #             "label": loc_code,
    #             "borderColor": f'rgba(128,128,128,.7)',
    #             "pointBorderColor": f'rgba(128,128,128,1)',
    #             "borderWidth": 10,
    #             "data": [{
    #                 "x": session["index_filter"]["start_date"], "y": i
    #             }, ],
    #         })
    #     i += 1

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
