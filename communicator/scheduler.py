from communicator import db, app
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from communicator.api import admin


def update_and_notify():
    with app.app_context():
        if app.config['RUN_SCHEDULED_TASKS']:
            admin._update_data()
            admin._notify_by_email()
            admin._notify_by_text()

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
