from communicator import db
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
scheduler.add_job(
    'communicator.api.admin:update_data', 'interval', minutes=10, id='update_data', replace_existing=True
)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())