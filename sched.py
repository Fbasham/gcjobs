from apscheduler.schedulers.background import BackgroundScheduler
import scrape

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', hours=1, start_date='2020-08-28 11:50:00')
def job():
    print('running scheduled scrape')
    scrape.main()

scheduler.start()
