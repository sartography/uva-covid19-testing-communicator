import os
import re
from os import environ

basedir = os.path.abspath(os.path.dirname(__file__))

JSON_SORT_KEYS = False  # CRITICAL.  Do not sort the data when returning values to the front end.

API_TOKEN = environ.get('API_TOKEN', default="CHANGE_THIS_IN_PROD")

NAME = "UVA Covid 19 Testing Communicator"
FLASK_PORT = environ.get('PORT0') or environ.get('FLASK_PORT', default="5000")
CORS_ALLOW_ORIGINS = re.split(r',\s*', environ.get('CORS_ALLOW_ORIGINS', default="localhost:4200, localhost:5002"))
TESTING = environ.get('TESTING', default="false") == "true"
PRODUCTION = (environ.get('PRODUCTION', default="false") == "true")
ADMINS = environ.get('ADMINS', default="testUser")

# Sentry flag
ENABLE_SENTRY = environ.get('ENABLE_SENTRY', default="false") == "true"  # To be removed soon
SENTRY_ENVIRONMENT = environ.get('SENTRY_ENVIRONMENT', None)

# Add trailing slash to base path, typically this would be something like "/api/" don't use the full path!
APPLICATION_ROOT = re.sub(r'//', '/', '/%s/' % environ.get('APPLICATION_ROOT', default="/").strip('/'))
# The full path to get to this, this is what would be returned form flask's request.url_root, but we won't
# have access to that in scheduled tasks run outside a request, this should include and match the APPLICATION_ROOT
# with no trailing backslask
URL_ROOT = environ.get('URL_ROOT', default="http://localhost:5000")
FRONT_END_URL = environ.get('FRONT_END_URL', default="http://localhost:4200")


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
DELETE_IVY_FILES = environ.get('DELETE_IVY_FILES', default="false") == "true"

# NOT IN USE -- Globus endpoint connections - These are not currently used, setting defaults so we don't need to include them
# in our Docker container.
GLOBUS_CLIENT_ID = environ.get('GLOBUS_CLIENT_ID', default="NA")
GLOBUS_TRANSFER_RT = environ.get('GLOBUS_TRANSFER_RT', default="NA")
GLOBUS_TRANSFER_AT = environ.get('GLOBUS_TRANSFER_AT', default="NA")
GLOBUS_IVY_ENDPOINT = environ.get('GLOBUS_IVY_ENDPOINT', default="NA")
GLOBUS_DTN_ENDPOINT = environ.get('GLOBUS_DTN_ENDPOINT', default="NA")
GLOBUS_IVY_PATH = environ.get('GLOBUS_IVY_PATH', default="NA")
GLOBUS_DTN_PATH = environ.get('GLOBUS_DTN_PATH', default="NA")

# NOT IN USE --  Twilio SMS Messages
TWILIO_SID = environ.get('TWILIO_SID', default="NA")
TWILIO_TOKEN = environ.get('TWILIO_TOKEN', default="NA")
TWILIO_NUMBER =  environ.get('TWILIO_NUMBER', default="NA")

# NOT IN USE --  Firestore configuration
FIRESTORE_JSON = environ.get('FIRESTORE_JSON', default="NA")

# Scheduled tasks
SCHEDULED_TASK_MINUTES = float(environ.get('SCHEDULED_TASK_MINUTES', default=1))
RUN_SCHEDULED_TASKS = environ.get('RUN_SCHEDULED_TASKS', default="false") == "true"

# Argon Settings
CSRF_ENABLED = True
SECRET_KEY = environ.get('SECRET_KEY', default="Shhhh!!! This is secret!  And better darn well not show up in prod.")
