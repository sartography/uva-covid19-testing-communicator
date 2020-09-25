import os
import re
from os import environ

basedir = os.path.abspath(os.path.dirname(__file__))

JSON_SORT_KEYS = False  # CRITICAL.  Do not sort the data when returning values to the front end.

NAME = "UVA Covid 19 Testing Communicator"
FLASK_PORT = environ.get('PORT0') or environ.get('FLASK_PORT', default="5000")
CORS_ALLOW_ORIGINS = re.split(r',\s*', environ.get('CORS_ALLOW_ORIGINS', default="localhost:4200, localhost:5002"))
TESTING = environ.get('TESTING', default="false") == "true"
PRODUCTION = (environ.get('PRODUCTION', default="false") == "true")

# Sentry flag
ENABLE_SENTRY = environ.get('ENABLE_SENTRY', default="false") == "true"  # To be removed soon
SENTRY_ENVIRONMENT = environ.get('SENTRY_ENVIRONMENT', None)

# Add trailing slash to base path
APPLICATION_ROOT = re.sub(r'//', '/', '/%s/' % environ.get('APPLICATION_ROOT', default="/").strip('/'))

DB_HOST = environ.get('DB_HOST', default="localhost")
DB_PORT = environ.get('DB_PORT', default="5433")
DB_NAME = environ.get('DB_NAME', default="communicator_dev")
DB_USER = environ.get('DB_USER', default="communicator_user")
DB_PASSWORD = environ.get('DB_PASSWORD', default="communicator_pass")
SQLALCHEMY_DATABASE_URI = environ.get(
    'SQLALCHEMY_DATABASE_URI',
    default="postgresql://%s:%s@%s:%s/%s" % (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
)
SQLALCHEMY_TRACK_MODIFICATIONS=False
TOKEN_AUTH_TTL_HOURS = float(environ.get('TOKEN_AUTH_TTL_HOURS', default=24))
SECRET_KEY = environ.get('SECRET_KEY', default="Shhhh!!! This is secret!  And better darn well not show up in prod.")
SWAGGER_AUTH_KEY = environ.get('SWAGGER_AUTH_KEY', default="SWAGGER")

# Github settings
GITHUB_TOKEN = environ.get('GITHUB_TOKEN', None)
GITHUB_REPO = environ.get('GITHUB_REPO', None)
TARGET_BRANCH = environ.get('TARGET_BRANCH', None)

# Email configuration
MAIL_DEBUG = environ.get('MAIL_DEBUG', default="false") == "true"
MAIL_SERVER = environ.get('MAIL_SERVER', default='smtp.mailtrap.io')
MAIL_PORT = environ.get('MAIL_PORT', default=2525)
MAIL_USE_SSL = environ.get('MAIL_USE_SSL', default="false") == "true"
MAIL_USE_TLS = environ.get('MAIL_USE_TLS', default="false") == "true"
MAIL_USERNAME = environ.get('MAIL_USERNAME', default='')
MAIL_PASSWORD = environ.get('MAIL_PASSWORD', default='')
MAIL_SENDER = 'UVA Prevalence Testing <Prevalence-Test@virginia.edu>'
MAIL_TIMEOUT = 10

# Ivy Directory
IVY_IMPORT_DIR = environ.get('IVY_IMPORT_DIR', default='')

# Globus endpoint connections
GLOBUS_CLIENT_ID = environ.get('GLOBUS_CLIENT_ID')
GLOBUS_TRANSFER_RT = environ.get('GLOBUS_TRANSFER_RT')
GLOBUS_TRANSFER_AT = environ.get('GLOBUS_TRANSFER_AT')
GLOBUS_IVY_ENDPOINT = environ.get('GLOBUS_IVY_ENDPOINT')
GLOBUS_DTN_ENDPOINT = environ.get('GLOBUS_DTN_ENDPOINT')

# Twilio SMS Messages
TWILIO_SID = environ.get('TWILIO_SID')
TWILIO_TOKEN = environ.get('TWILIO_TOKEN')
TWILIO_NUMBER =  environ.get('TWILIO_NUMBER')

# Firestore configuration
FIRESTORE_JSON = environ.get('FIRESTORE_JSON')

# Scheduled tasks
SCHEDULED_TASK_MINUTES = float(environ.get('SCHEDULED_TASK_MINUTES', default=10))
