import csv
import io
import json

import logging
import os
from datetime import datetime
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
from sentry_sdk.integrations.flask import FlaskIntegration
from webassets import Bundle
from flask_executor import Executor

import numpy as np
import matplotlib.pyplot as plt

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

from communicator import models
from communicator import api
from communicator import forms
import random 
# from communicator import scheduler

connexion_app.add_api('api.yml', base_path='/v1.0')

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


@app.route('/', methods=['GET', 'POST'])
@superuser
def index():
    from communicator.models import Sample
    from communicator.tables import SampleTable

    download = False

    form = forms.SearchForm(request.form)
    action = BASE_HREF + "/"
    samples = db.session.query(Sample).order_by(Sample.date.desc())

    if request.method == "POST" or request.args.get('cancel') == 'true':
        session["index_filter"] = {}  # Clear out the session if it is invalid.

    if form.validate():
        session["index_filter"] = {}
        if form.startDate.data:
            session["index_filter"]["start_date"] = form.startDate.data
        else:
            from datetime import date
            session["index_filter"]["start_date"] = date.today()
        if form.endDate.data:
            session["index_filter"]["end_date"] = form.endDate.data
        if form.studentId.data:
            session["index_filter"]["student_id"] = form.studentId.data
        if form.location.data:
            session["index_filter"]["location"] = form.location.data
        if form.email.data:
            session["index_filter"]["email"] = form.email.data
        if form.download.data:
            download = True

    # # Store previous form submission settings in the session, so they are preseved through pagination.
    if "index_filter" in session:
        filters = session["index_filter"]
        try:
            if "start_date" in filters:
                samples = samples.filter(Sample.date >= filters["start_date"])
            if "end_date" in filters:
                samples = samples.filter(Sample.date <= filters["end_date"])
            if "student_id" in filters:
                samples = samples.filter(
                    Sample.student_id.in_(filters["student_id"].split()))
            if "location" in filters:
                samples = samples.filter(
                    Sample.location.in_(filters["location"].split()))
            if "email" in filters:
                samples = samples.filter(
                    Sample.email.ilike(filters["email"] + "%"))
        except Exception as e:
            logging.error(
                "Encountered an error building filters, so clearing. " + e)
            session["index_filter"] = {}

    # display results
    if download:
        csv = __make_csv(samples)
        return send_file(csv, attachment_filename='data_export.csv', as_attachment=True)

    else:
        page = request.args.get(get_page_parameter(), type=int, default=1)
        pagination = Pagination(page=page, total=samples.count(
        ), search=False, record_name='samples', css_framework='bootstrap4')

        table = SampleTable(samples.paginate(page, 10, error_out=False).items)

        chart_data = {"datasets": []}
        # Get Active Locations Info 
        active_stations = ["10", "20", "30", "40", "50", "60"]
        # https://stackoverflow.com/questions/19442224/getting-information-for-bins-in-matplotlib-histogram-function
       

        # Seperate Data
        location_data = dict()
        sample_times = dict()

        for entry in samples:
            loc_code = str(entry.location)[:2]
            if loc_code not in location_data:
                location_data[loc_code] = [entry]
                sample_times[loc_code] = [entry.date.timestamp()]
                logging.info(entry.date)
            else:
                location_data[loc_code].append(entry)
                sample_times[loc_code].append(entry.date.timestamp())
        # Analysis
        i = 0
        for loc_code in location_data.keys():
            data_dict = dict({
                "label": loc_code,
                "borderColor": f'rgba(255,{i*50},{i*20},.7)',
                "pointBorderColor": f'rgba(255,{i*50},{i*20},1)',
                "borderWidth": 10,
                "data": [],
            })

            hist, bin_edges = np.histogram(np.array(sample_times[loc_code]))#, dtype = np.int64))
            #bin_edges = [datetime.fromtimestamp(date) for date in bin_edges]
            bins = [bin_edges[i]+(bin_edges[i+1]-bin_edges[i])/2 for i in range(len(bin_edges)-1)]
        
            for cnt, date in zip(hist,bins):
                data_dict["data"].append({
                    "x": datetime.utcfromtimestamp(date), "y": int(cnt)
                })

            chart_data["datasets"].append(data_dict)
            i += 1
        # Check for Unresponsive
        for loc_code in active_stations:
            if loc_code not in location_data:
                chart_data["datasets"].append({
                    "label": loc_code,
                    "borderColor": f'rgba(128,128,128,.7)',
                    "pointBorderColor": f'rgba(128,128,128,1)',
                    "borderWidth": 10,
                    "data": [{
                        "x": session["index_filter"]["start_date"], "y": i
                    }, ],
                })
            i += 1
        return render_template('layouts/default.html',
                               base_href=BASE_HREF,
                               content=render_template(
                                   'pages/index.html',
                                   form=form,
                                   table=table,
                                   action=action,
                                   pagination=pagination,
                                   description_map={},
                                   chart_data=chart_data
                               ))


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
