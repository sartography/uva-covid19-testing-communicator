import os
from apscheduler.schedulers.blocking import BlockingScheduler
from communicator import db

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_jobstore('sqlalchemy', url=db.engine.url)
    scheduler.add_job(
        'communicator.api.admin:update_data', 'interval', minutes=10,
         id='update_data', replace_existing=True
    )

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
