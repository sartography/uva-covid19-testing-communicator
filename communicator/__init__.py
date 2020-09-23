import logging
import os

import connexion
import sentry_sdk
from flask import render_template, request
from flask_assets import Environment
from flask_cors import CORS
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

# Configuration
app.config.from_object('config.default')
if "TESTING" in os.environ and os.environ["TESTING"] == "true":
    app.config.from_object('config.testing')
    app.config.from_pyfile('../config/testing.py')
else:
    app.config.root_path = app.instance_path
    app.config.from_pyfile('config.py', silent=True)

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
    'scss/app.scss',
    filters='pyscss',
    output='app.css'
)
assets.register('app_scss', scss)

from communicator import models
from communicator import api
from communicator import forms

connexion_app.add_api('api.yml', base_path='/v1.0')

# Convert list of allowed origins to list of regexes
origins_re = [r"^https?:\/\/%s(.*)" % o.replace('.', '\.') for o in app.config['CORS_ALLOW_ORIGINS']]
cors = CORS(connexion_app.app, origins=origins_re)

# Sentry error handling
if app.config['SENTRY_ENVIRONMENT']:
    sentry_sdk.init(
        environment=app.config['SENTRY_ENVIRONMENT'],
        dsn="https://25342ca4e2d443c6a5c49707d68e9f40@o401361.ingest.sentry.io/5260915",
        integrations=[FlaskIntegration()]
    )

### HTML Pages
BASE_HREF = app.config['APPLICATION_ROOT'].strip('/')


@app.route('/', methods=['GET'])
def index():
    from communicator.models import Sample
    from communicator.tables import SampleTable
    # display results
    page = request.args.get(get_page_parameter(), type=int, default=1)
    samples = db.session.query(Sample).order_by(Sample.date.desc())
    pagination = Pagination(page=page, total=samples.count(), search=False, record_name='samples')

    table = SampleTable(samples.paginate(page,10,error_out=False).items)
    return render_template(
        'index.html',
        table=table,
        pagination=pagination,
        base_href=BASE_HREF
    )

@app.route('/invitation', methods=['GET', 'POST'])
def send_invitation():
    from communicator.models.invitation import Invitation
    from communicator.tables import InvitationTable

    form = forms.InvitationForm(request.form)
    action = BASE_HREF + "/invitation"
    title = "Send invitation to students"
    if request.method == 'POST' and form.validate():
        from communicator.services.notification_service import NotificationService
        with NotificationService(app) as ns:
            ns.send_invitations(form.date.data, form.location.data, form.emails.data)

    # display results
    page = request.args.get(get_page_parameter(), type=int, default=1)
    invites = db.session.query(Invitation).order_by(Invitation.date.desc())
    pagination = Pagination(page=page, total=invites.count(), search=False, record_name='samples')

    table = InvitationTable(invites.paginate(page,10,error_out=False).items)

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
def list_imported_files_from_ivy():
    from communicator.models.ivy_file import IvyFile
    from communicator.tables import IvyFileTable

    # display results
    page = request.args.get(get_page_parameter(), type=int, default=1)
    files = db.session.query(IvyFile).order_by(IvyFile.date_added.desc())
    pagination = Pagination(page=page, total=files.count(), search=False, record_name='samples')

    table = IvyFileTable(files.paginate(page, 10, error_out=False).items)
    return render_template(
        'imported_files.html',
        table=table,
        pagination=pagination,
        base_href=BASE_HREF
    )

@app.route('/sso')
def sso():
    response = ""
    response += "<h1>Headers</h1>"
    response += "<ul>"
    for k, v in request.headers:
        response += "<li><b>%s</b> %s</li>\n" % (k, v)
    response += "<h1>Environment</h1>"
    for k, v in request.environ:
        response += "<li><b>%s</b> %s</li>\n" % (k, v)
    return response

# Access tokens
@app.cli.command()
def globus_token():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    ivy_service.get_access_token()


@app.cli.command()
def list_files():
    from communicator.services.ivy_service import IvyService
    ivy_service = IvyService()
    ivy_service.list_files()


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
