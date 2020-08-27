from apscheduler.schedulers.blocking import BlockingScheduler
import scrape

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=4, start_date='2020-08-27 17:30:00')
def job():
    print('running scheduled scrape')
    scrape.main()

scheduler.start()
