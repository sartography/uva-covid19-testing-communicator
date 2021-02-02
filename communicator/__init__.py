import csv
import csv
import io
import json
import logging
import os
from datetime import datetime
from functools import wraps

import connexion
import numpy as np
import sentry_sdk
from babel.dates import format_datetime, get_timezone
from flask import render_template, request, redirect, url_for, flash, abort, Response, send_file, session
from flask_assets import Environment
from flask_cors import CORS
from flask_executor import Executor
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_paginate import Pagination, get_page_parameter
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration
from webassets import Bundle

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

from communicator import models
from communicator import api
from communicator import forms
from communicator.models import Sample, Deposit
from communicator.tables import SampleTable, InventoryDepositTable
from communicator import scheduler # Must import this to cause the scheduler to kick off.

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
    return render_template('layouts/default.html',
        base_href="/",
        content=render_template('pages/404.html'))

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

from communicator.services.graph_service import GraphService, daterange
from datetime import timedelta

@app.route('/', methods=['GET', 'POST'])
@superuser
def index():
    form = forms.SearchForm(request.form)
    action = BASE_HREF + "/"
    graph = GraphService()

    if request.method == "POST": session["index_filter"] = {}  # Clear out the session if it is invalid.
    if "index_filter" not in session: session["index_filter"] = {}
    if form.validate():
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
        if form.include_tests.data:
            session["index_filter"]["include_tests"] = form.include_tests.data

    if type(session["index_filter"].get("start_date", None)) == str:
        session["index_filter"]["start_date"] = datetime.strptime(session["index_filter"]["start_date"].strip(), "%Y-%m-%d").date()
    if type(session["index_filter"].get("end_date",None)) == str:
        session["index_filter"]["end_date"] = datetime.strptime(session["index_filter"]["end_date"].strip(), "%Y-%m-%d").date()

    graph.update_search_filters(session["index_filter"])

    samples = db.session.query(Sample).order_by(Sample.date.desc())
    filtered_samples = graph.apply_filters(samples)
    if request.args.get('download') == 'true':
        csv = __make_csv(filtered_samples)
        return send_file(csv, attachment_filename='data_export.csv', as_attachment=True)

    overall_chart_data = {
        "daily":{},
        "hourly":{},
        "weekday":{}
        }

    overall_totals_data = {
                    "one_week_ago" : 0,
                    "two_week_ago" : 0,
                    "search" : 0,
                }
    
    chart_ticks = [] 
    timeFormat = "%m/%d"
    bounds = daterange(graph.start_date, graph.end_date, days=1, hours=0)
    for i in range(len(bounds) - 1):
        chart_ticks.append(f"{bounds[i].strftime(timeFormat)}")
    
    location_stats_data = graph.get_totals_last_week()
    hourly_charts_data = graph.get_totals_by_hour()
    daily_charts_data = graph.get_totals_by_day()
    weekday_charts_data = graph.get_totals_by_weekday()

    # Aggregate results 
    for location in location_stats_data:     
        if location in daily_charts_data:
            overall_chart_data["daily"][location] = np.sum([daily_charts_data[location][station] for station in daily_charts_data[location]],axis=0,dtype=np.int).tolist()
            overall_chart_data["hourly"][location] = np.sum([hourly_charts_data[location][station] for station in hourly_charts_data[location]],axis=0,dtype=np.int).tolist()
            overall_chart_data["weekday"][location] = np.sum([weekday_charts_data[location][station] for station in weekday_charts_data[location]],axis=0,dtype=np.int).tolist()
        
        overall_totals_data["one_week_ago"] += location_stats_data[location]["one_week_ago"]
        overall_totals_data["two_week_ago"] += location_stats_data[location]["two_week_ago"]
        overall_totals_data["search"] += location_stats_data[location]["search"]

    important_dates = {
        "search" : graph.start_date.strftime("%m/%d/%Y") + " - " + (graph.end_date - timedelta(1)).strftime("%m/%d/%Y"),
        "one_week_ago" : (graph.start_date - timedelta(7)).strftime("%m/%d/%Y") + " - " + (graph.end_date- timedelta(8)).strftime("%m/%d/%Y"),
        "two_weeks_ago" : (graph.start_date - timedelta(14)).strftime("%m/%d/%Y") + " - " + (graph.end_date - timedelta(15)).strftime("%m/%d/%Y"),
        }
    ################# Raw Samples Table ##############
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=filtered_samples.count(
    ), search=False, record_name='samples', css_framework='bootstrap4')
    
    table = SampleTable(group_columns(filtered_samples[(page - 1) * 10:((page - 1) * 10) + 10]))
    
    return render_template('layouts/default.html',
                            base_href=BASE_HREF,
                            dates = important_dates,
                            overall_totals_data = overall_totals_data,
                            content=render_template(
                               'pages/index.html',
                               form = form,
                               dates = important_dates,
                               table = table,
                               action = action,
                               pagination = pagination,

                               chart_ticks = chart_ticks,
                               overall_chart_data = overall_chart_data,
                               daily_charts_data = daily_charts_data,
                               hourly_charts_data = hourly_charts_data,
                               weekday_charts_data = weekday_charts_data,
                               
                            
                               overall_totals_data = overall_totals_data,
                               location_stats_data = location_stats_data,
                           ))

@app.route('/inventory', methods=['GET', 'POST'])
@superuser
def inventory_page():
    form = forms.InventoryDepositForm(request.form)
    if form.validate():
        if form.date_added.data != None and form.amount.data != None:
            _date = datetime.strptime(form.date_added.data.strip(), "%m/%d/%Y").date()
            new_deposit = Deposit(date_added=_date, amount=int(form.amount.data), notes=form.notes.data)
            db.session.add(new_deposit)
            db.session.commit()    
    deposits = db.session.query(Deposit).order_by(Deposit.date_added.desc())
    total_deposits = sum([i.amount for i in deposits])
    if deposits.count() > 0:
        sample_count = db.session.query(Sample).filter(Sample.date >= deposits[-1].date_added).count()
        first_deposit = deposits[-1].date_added.strftime("%m/%d/%Y")
    else:
        sample_count = 0
        first_deposit = "(No Deposits)"
    samples_since = total_deposits - sample_count
    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page = page, total = deposits.count(),\
        search = False, record_name = 'deposits', css_framework = 'bootstrap4')

    return render_template('layouts/default.html',
                           base_href=BASE_HREF,
                           content=render_template(
                               'pages/inventory.html',
                               form=form,
                               pagination = pagination,
                               samples_since = samples_since,
                               first_deposit = first_deposit,
                               deposits = deposits[(page - 1) * 10:((page - 1) * 10) + 10]))


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
                            search=False, record_name='samples', css_framework='bootstrap4')

    table = IvyFileTable(files.paginate(page, 10, error_out=False).items)
    return render_template('layouts/default.html',
                           base_href=BASE_HREF,
                           content=render_template(
                               'pages/imported_files.html',
                               table=table,
                               pagination=pagination,
                               base_href=BASE_HREF
                           ))


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
