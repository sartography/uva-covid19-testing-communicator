from datetime import datetime

import pytz

from communicator import db, app
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from communicator.api import admin


def within_notification_window():
    tz = pytz.timezone('US/Eastern')
    now = (datetime.now(tz))
    one_pm = (datetime.now(tz).replace(hour=13, minute=0, second=0, microsecond=0))
    two_pm = (datetime.now(tz).replace(hour=17, minute=30, second=0, microsecond=0))
    return one_pm <= now <= two_pm


def update():
    with app.app_context():
        # Do not request IVY transfers, they happen automatically, just load the local files if they exist,
        # and send any emails that need sending.
        admin.load_local_files()
        admin._notify_by_email()


if app.config['RUN_SCHEDULED_TASKS']:
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
    scheduler.add_job(
        update, 'interval', minutes=app.config['SCHEDULED_TASK_MINUTES'],
        id='update', replace_existing=True
    )
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
else:
    app.logger.info("Currently not running scheduled tasks RUN_SCHEDULED_TASKS"
                    " is set to false in configuration.")
