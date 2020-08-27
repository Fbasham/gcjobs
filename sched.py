from apscheduler.schedulers.blocking import BlockingScheduler
import foo

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=12, start_date='2020-08-27 12:32:00')
def job():
    print('running scheduled scrape')
    foo.main()

scheduler.start()
