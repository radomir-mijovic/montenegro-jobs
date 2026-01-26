import logging

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job
from app.scrapers import get_scraper
from app.scrapers.base import Job as JobCreate
from celery import group
from sqlmodel import select

logger = logging.getLogger(__name__)

SOURCES: dict[str, int] = {
    "prekoveze": 1,
    "zaposlime": 2,
    "zzzcg": 1,
}


@celery_app.task(name="app.tasks.scrape_single_source", bind=True, max_retries=3)
def scrape_single_source(self, source: str, max_pages: int):
    """Scrape a single job source"""
    logger.info(f"Starting scraping job for {source}")

    session = SessionLocal()
    try:
        try:
            scraper = get_scraper(scraper=source)
            jobs = scraper.scrape(max_pages=max_pages)

            if jobs:
                existing_by_url = get_existing_jobs_url(jobs, session)
                save_jobs(jobs, existing_by_url, session)

            logger.info(f"Job scraping completed. Results: {len(jobs) if jobs else 0}")
            return {
                "source": source,
                "jobs_count": len(jobs) if jobs else 0,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error while scpaing {source}: {e}")
            raise self.retry(exc=e, countdown=300)
    finally:
        session.close()


@celery_app.task(name="app.tasks.scrape_all_jobs")
def scrape_all_jobs():
    """Coordinator taks that triggers all scrapers in parralel"""
    job = group(
        scrape_single_source.s(source, max_pages)
        for source, max_pages in SOURCES.items()
    )
    return job.apply_async()


def save_jobs(jobs: list[JobCreate], existing_by_url: dict, session) -> None:
    for job_data in jobs:
        existing = existing_by_url.get(job_data.url)
        if existing is None:
            session.add(Job(**job_data.model_dump()))
            continue

        updated: bool = False

        if existing.expires != job_data.expires:
            existing.expires = job_data.expires
            updated = True

        if updated:
            session.add(existing)

    session.commit()


def get_existing_jobs_url(jobs: list[JobCreate], session) -> dict:
    urls = [job.url for job in jobs]
    existing_jobs = session.exec(select(Job).where(Job.url.in_(urls))).all()
    return {job.url: job for job in existing_jobs}
