from communicator import db, app
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from communicator.api import admin


def update_and_notify():
    with app.app_context():
        admin.update_and_notify()

scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
scheduler.add_job(
    update_and_notify, 'interval', minutes=app.config['SCHEDULED_TASK_MINUTES'],
#    update_and_notify, 'interval', seconds=5,
    id='update_data', replace_existing=True
)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())