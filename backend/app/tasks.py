from app.celery_app import celery_app

@celery_app.task(name="app.tasks.scrape_jobs")
def scrape_jobs():
    return "Jobs scraped successfully"
