import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

celery_app: Celery = Celery(
    "montengro-jobs", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Podgorica",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)

celery_app.conf.beat_schedule = {
    "scrape-jobs-morning": {
        "task": "app.tasks.scrape_all_jobs",
        "schedule": crontab(hour=8, minute=0),
    },
    "scrape-jobs-noon": {
        "task": "app.tasks.scrape_all_jobs",
        "schedule": crontab(hour=12, minute=0),
    },
    "scrape-jobs-afternoon": {
        "task": "app.tasks.scrape_all_jobs",
        "schedule": crontab(hour=17, minute=0),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
