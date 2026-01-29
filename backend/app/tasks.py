import logging
import os

import redis
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job
from app.scrapers import get_scraper
from app.scrapers.base import Job as JobCreate
from app.scrapers.prekoveze import last_page_number as prekoveze_last_page_number
from app.scrapers.zaposlime import last_page_number as zaposlime_last_page_number
from celery import chord
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

# Get Redis URL from environment variable
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

SOURCES: dict[str, int | None] = {
    "prekoveze": prekoveze_last_page_number if prekoveze_last_page_number else 20,
    "zaposlime": zaposlime_last_page_number if zaposlime_last_page_number else 40,
    "zzzcg": 55,
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
                # adding new jobs url in redis so that expired ones can be deleted
                redis_client.sadd("current_scraped_urls", *[job.url for job in jobs])

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
    job = chord(
        (
            scrape_single_source.s(source, max_pages)
            for source, max_pages in SOURCES.items()
        ),
        cleanup_expired_jobs.s(),
    )
    return job.apply_async()


@celery_app.task(name="app.tasts.cleanup_expired_jobs")
def cleanup_expired_jobs(results):
    """Runs after all scrapers complete to delete expired jobs"""
    session = SessionLocal()
    try:
        delete_expired_ones_from_database(session)
        redis_client.delete("current_scraped_urls")
        logger.info("Cleant up finished")
    finally:
        session.close()


def save_jobs(jobs: list[JobCreate], existing_by_url: dict, session: Session) -> None:
    saved: int = 0
    updated: int = 0
    skipped: int = 0

    for job_data in jobs:
        existing = existing_by_url.get(job_data.url)

        if existing is None:
            try:
                session.add(Job(**job_data.model_dump()))
                session.commit()
                saved += 1
            except IntegrityError:
                session.rollback()
                logger.warning(f"Duplicated URL skipped: {job_data.url}")
            continue

        is_updated: bool = False

        if existing.expires != job_data.expires:
            existing.expires = job_data.expires
            is_updated = True

        if is_updated:
            try:
                session.add(existing)
                session.commit()
                updated += 1
            except IntegrityError:
                session.rollback()
                skipped += 1

    logger.info(f"Saved {saved}, Updated: {updated}, Skipped: {skipped}")


def get_existing_jobs_url(jobs: list[JobCreate], session) -> dict:
    urls = [job.url for job in jobs]
    existing_jobs = session.exec(select(Job).where(Job.url.in_(urls))).all()
    return {job.url: job for job in existing_jobs}


def delete_expired_ones_from_database(session: Session) -> None:
    jobs = session.exec(select(Job)).all()
    existing = {job.url for job in jobs}
    new_urls_from_scrape = redis_client.smembers("current_scraped_urls")

    if existing and new_urls_from_scrape:
        expired = existing - new_urls_from_scrape  # type: ignore

        if expired:
            query = select(Job).where(Job.url.in_(expired))
            jobs_to_delete = session.exec(query).all()

            for job in jobs_to_delete:
                logger.info(f"Deleted expired job: {job}")
                session.delete(job)

        session.commit()
