from communicator import db, app
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
scheduler.add_job(
    'communicator.api.admin:update_and_notify', 'interval', minutes=app.config['SCHEDULED_TASK_MINUTES'],
    id='update_data', replace_existing=True
)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())