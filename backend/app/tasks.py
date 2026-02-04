import json
import logging
from datetime import date

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job
from app.models.job import Category
from app.models.utils import CATEGORY_KEYWORDS
from app.redis_app import JOB_CACHE_KEY, JOB_CACHE_TTL
from app.redis_app import redis as redis_app
from app.scrapers import get_scraper
from app.scrapers.base import Job as JobCreate
from app.scrapers.prekoveze import last_page_number as prekoveze_last_page_number
from app.scrapers.zaposlime import last_page_number as zaposlime_last_page_number
from celery import chord
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, func, select

logger = logging.getLogger(__name__)


SOURCES: dict[str, int | None] = {
    "prekoveze": prekoveze_last_page_number if prekoveze_last_page_number else 20,
    "zaposlime": zaposlime_last_page_number if zaposlime_last_page_number else 40,
    "zzzcg": 55,
    "radnikme": 1,
    "berzarada": 4,
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
    job = chord(
        (
            scrape_single_source.s(source, max_pages)
            for source, max_pages in SOURCES.items()
        ),
        (
            cleanup_expired_jobs.s()
            | delete_duplicated_jobs.s()
            | cache_all_jobs.s()
            | assign_categories_to_jobs.s()
        ),
    )
    return job.apply_async()


@celery_app.task(name="app.tasks.cleanup_expired_jobs")
def cleanup_expired_jobs(results):
    """Runs after all scrapers complete to delete expired jobs"""
    session = SessionLocal()
    try:
        delete_expired_ones_from_database(session)
        logger.info("Cleant up finished")
    finally:
        session.close()


@celery_app.task(name="app.tasks.delete_duplicated_jobs")
def delete_duplicated_jobs(results):
    """Runs just in case if there is any duplicated jobs"""
    session = SessionLocal()
    try:
        query = select(func.min(Job.id)).group_by(Job.url)
        stmt = delete(Job).where(Job.id.not_in(query))
        result = session.exec(stmt)
        session.commit()
        logger.info(f"Deleted {result.rowcount} duplicated jobs")
    finally:
        session.close()


@celery_app.task(name="app.tasks.cache_all_jobs")
def cache_all_jobs(results):
    """Runs after all jobs to cache all new jobs"""
    session = SessionLocal()
    try:
        redis_app.delete(JOB_CACHE_KEY)
        logger.info(f"Deleted existing cache for key: {JOB_CACHE_KEY}")

        all_jobs = session.exec(select(Job)).all()
        redis_app.set(
            JOB_CACHE_KEY,
            json.dumps([job.model_dump(mode="json") for job in all_jobs]),
            ex=JOB_CACHE_TTL,
        )
        logger.info(f"Cached {len(all_jobs)} jobs")
    finally:
        session.close()


@celery_app.task(name="app.tasks.assign_categories_to_jobs")
def assign_categories_to_jobs(results):
    session = SessionLocal()

    try:
        categories = session.exec(select(Category)).all()
        category_map: dict = {cat.name: cat for cat in categories}

        jobs = session.exec(select(Job)).all()

        for job in jobs:
            job_title_lower: str = job.title.lower()
            matched_categories: list = []

            for category_name, keywords in CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in job_title_lower:
                        if category_name in category_map:
                            category = category_map[category_name]

                            if category not in matched_categories:
                                matched_categories.append(category)
                        break

            if matched_categories:
                job.categories = matched_categories
                session.add(job)

        session.commit()

    except Exception as e:
        logger.warning(f"Error while assigning category: {e}")

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
    query = select(Job).where(
        Job.expires.is_not(None),  # type: ignore
        Job.expires < date.today(),  # type: ignore
    )
    jobs_to_delete = session.exec(query).all()

    if jobs_to_delete:
        for job in jobs_to_delete:
            logger.info(f"Deleted expired job: {job.title}, expired: {job.expires}")
            session.delete(job)

        session.commit()
        logger.info(f"Deleted {len(jobs_to_delete)} expired jobs")
    else:
        logger.info("No expired jobs to delete")


def create_all_categories_in_db():
    session = SessionLocal()

    try:
        for key in CATEGORY_KEYWORDS.keys():
            query = select(Category).where(Category.name == key)
            if session.exec(query).first():
                continue
            else:
                category = Category(name=key)
                session.add(category)
                session.commit()
    except Exception as e:
        logger.warning(f"Error on creating category: {e}")

    finally:
        session.close()
