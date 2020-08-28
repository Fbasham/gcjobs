from apscheduler.schedulers.blocking import BlockingScheduler
import scrape

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=1, start_date='2020-08-28 12:00:00')
def job():
    print('running scheduled scrape')
    scrape.main()

scheduler.start()
