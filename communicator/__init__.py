import logging
import os

import connexion
import sentry_sdk
from flask_cors import CORS
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration


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

from communicator import models
from communicator import api
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
