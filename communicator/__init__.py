
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

from communicator import forms
from communicator import api
from communicator import models
from datetime import date, timedelta

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
        if form.startDate.data:
            session["index_filter"]["start_date"] = form.startDate.data
        if form.endDate.data:
            session["index_filter"]["end_date"] = form.endDate.data
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
                filtered_samples = filtered_samples.filter(
                    Sample.date >= date.today())
                filters["start_date"] = date.today()
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

    if request.args.get('download') == 'true':
        csv = __make_csv(filtered_samples)
        return send_file(csv, attachment_filename='data_export.csv', as_attachment=True)

    ############# Build Graphs ######################
    # Analysis
    station_charts = []
    location_chart = {"datasets": []}
    loc_sat_data = dict()
    station_stats = dict()  # {dict(), ...}

    today = date.today()
    one_week_ago = filters["end_date"] - timedelta(7)
    two_weeks_ago = one_week_ago - timedelta(7)

    weekday_totals = [0 for _ in range(7)]  # Mon, Tues, ...
    hour_totals = [0 for _ in range(24)]  # 12AM, 1AM, ...
    ############# Helper Variables ################## 
    if filtered_samples.count() > 0:
        date_range = (
            filtered_samples[-1].date.timestamp(), filtered_samples[0].date.timestamp())
        
    # Get Active Locations Info
    active_stations = ["10", "20", "30", "40", "50", "60"]
    location_stats = dict()

    # Seperate Data by location and station
    loc_sat_data = dict()
    sample_times = dict()

    # Sort Data
    for entry in filtered_samples:
        loc_code = str(entry.location)[:2]
        stat_code = str(entry.location)[2:]

        weekday_totals[entry.date.weekday()] += 1
        hour_totals[entry.date.hour] += 1
        # When iterating through the initial quarry if this
        # location has yet to be seen add it to the data set and if it has continue to update it
        if loc_code not in loc_sat_data:
            loc_sat_data[loc_code] = dict()
            sample_times[loc_code] = []

        if stat_code not in loc_sat_data[loc_code]:
            loc_sat_data[loc_code][stat_code] = dict()
            loc_sat_data[loc_code][stat_code]["two_week_ago"] = 0
            loc_sat_data[loc_code][stat_code]["one_week_ago"] = 0
            loc_sat_data[loc_code][stat_code]["today"] = 0
            loc_sat_data[loc_code][stat_code]["total"] = 0
            loc_sat_data[loc_code][stat_code]["entries"] = []

        # The previous if statement has guaranteed that this will not return a key error
        #  as if the location code or station code or not present in the loc_sat_data dictionary
        # they will have been added by this point
        loc_sat_data[loc_code][stat_code]["total"] += 1
        loc_sat_data[loc_code][stat_code]["entries"].append(entry)
        sample_times[loc_code].append(entry.date.timestamp())
        if entry.date.date() >= two_weeks_ago:
            loc_sat_data[loc_code][stat_code]["two_week_ago"] += 1
            if entry.date.date() >= one_week_ago:
                loc_sat_data[loc_code][stat_code]["one_week_ago"] += 1
                if entry.date.date() >= today:
                    loc_sat_data[loc_code][stat_code]["today"] += 1

    station_stats = []
    general_today = 0
    general_one_week_ago = 0 
    general_two_week_ago = 0 
    general_total = 0 
    for loc_code in loc_sat_data:
        ############# Build histogram ###################
        color = [hash(loc_code), 128, (hash(loc_code) % 256 + 128) % 256]
        single_hist = dict({
            "label": loc_code,
            "borderColor": f'rgba({color[0]},{color[1]},{color[2]},.7)',
            "pointBorderColor": f'rgba({color[0]},{color[1]},{color[2]},1)',
            "borderWidth": 8,
            "data": [],
        })
        # https://stackoverflow.com/questions/19442224/getting-information-for-bins-in-matplotlib-histogram-function
        hist, bin_edges = np.histogram(
            np.array(sample_times[loc_code]), range=date_range)
        bins = [bin_edges[i]+(bin_edges[i+1]-bin_edges[i]) /
                2 for i in range(len(bin_edges)-1)]
        for cnt, time in zip(hist, bins):
            single_hist["data"].append({
                "x": datetime.utcfromtimestamp(time), "y": int(cnt)
            })
        location_chart["datasets"].append(single_hist)
        
        
        station_lines = []
        i = 0
        today = 0
        one_week_ago = 0 
        two_week_ago = 0 
        total = 0 
        for stat_code in loc_sat_data[loc_code]:
            ############## Station Stats ##############
            today += loc_sat_data[loc_code][stat_code]["today"] 
            one_week_ago += loc_sat_data[loc_code][stat_code]["one_week_ago"] 
            two_week_ago += loc_sat_data[loc_code][stat_code]["two_week_ago"] 
            total += loc_sat_data[loc_code][stat_code]["total"] 
            ############## Build Station Uptime Graph ##############
            i += 1
            station_lines.append({
                "label": stat_code,
                "borderColor": f'rgba(50,255,255,.7)',
                "pointBorderColor": f'rgba(50,255,255,1)',
                "borderWidth": 10,
                "data": [
                    {"x": loc_sat_data[loc_code][stat_code]["entries"][0].date, "y": i}, {
                        "x": loc_sat_data[loc_code][stat_code]["entries"][-1].date, "y": i},
                ]})
        station_charts.append({"datasets": station_lines, "labels": []})
        station_stats.append({
            "today":today,            
            "one_week_ago":round(one_week_ago/7,2),
            "two_week_ago":round(two_week_ago/14,2),
            "average":round(total/len(loc_sat_data[loc_code]),2),
        })
        general_today = today
        general_one_week_ago = one_week_ago
        general_two_week_ago += two_week_ago
        general_total += total 
    location_stats = {
            "today":general_today,            
            "one_week_ago":round(general_one_week_ago/7,2),
            "two_week_ago":round(general_two_week_ago/14,2),
            "average":general_total #round(total/len(loc_sat_data[loc_code]),2),
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
                               form=form,
                               show = request.args.get('currently_showing',-1), 
                               table=table,
                               action=action,
                               pagination=pagination,

                               location_data=location_chart,
                               station_data=station_charts,

                               station_stats=station_stats,  # List<dict>
                               location_stats=location_stats,

                               weekday_totals=weekday_totals,
                               hour_totals=hour_totals,
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
