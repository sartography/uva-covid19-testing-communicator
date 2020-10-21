from datetime import datetime

import pytz

from communicator import db, app
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from communicator.api import admin


def within_notification_window(self):
    """Where 'reasaonable' is between 8am and 10pm. """
    tz = pytz.timezone('US/Eastern')
    now = (datetime.now(tz))
    one_pm = (datetime.now(tz).replace(hour=13, minute=0, second=0, microsecond=0))
    two_pm = (datetime.now(tz).replace(hour=14, minute=0, second=0, microsecond=0))
    return one_pm <= now <= two_pm


def update_and_notify():
    with app.app_context():
        if app.config['RUN_SCHEDULED_TASKS']:
            admin._update_data()
            if within_notification_window():
                app.logger.info("Within Notification Window, sending messages.")
                admin._notify_by_email()
                admin._notify_by_text()
            else:
                app.logger.info("Not within the notification window, not sending messages.")


if app.config['RUN_SCHEDULED_TASKS']:
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
    scheduler.add_job(
        update_and_notify, 'interval', minutes=app.config['SCHEDULED_TASK_MINUTES'],
        id='update_data', replace_existing=True
    )

    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
else:
    app.logger.info("Currently not running scheduled tasks RUN_SCHEDULED_TASKS"
                            " is set to false in configuration.")
