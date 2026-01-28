from app.models.job import Job
from sqlalchemy import text
from sqlalchemy.sql import func
from sqlmodel import Session, select


def get_queried_jobs(
    *,
    title: str | None,
    city: str | None,
    limit: int,
    offset: int | None = None,
    session: Session,
):
    """Query jobs using PostgreSQL fuzzy search with trigram similarity.

        Searches for jobs by title and/or city using advanced PostgreSQL features:
        - Trigram similarity for fuzzy matching (handles typos)
        - ILIKE pattern matching for substring searches
        Results are ordered by relevance (similarity score).

        Args:
            title: Job title search term. Supports fuzzy matching and partial
    word matching. None to skip title filtering.
            city: City/location search term. Uses ILIKE pattern matching.
                None to skip location filtering.
            limit: Maximum number of jobs to return (fetches limit+1 internally
                to check for more results).
            offset: Number of results to skip for pagination. Defaults to None
                (treated as 0).
            session: SQLModel database session for executing queries.

        Returns:
            List of Job model instances matching the search criteria, ordered by
            relevance. May contain up to limit+1 jobs (caller should trim if needed).
    """

    query = select(Job)
    fetch_limit = limit + 1

    if title and city:
        sql = text("""
                   SELECT * FROM job
                   WHERE (similarity(title, :title) > 0.1 OR title ILIKE :title_pattern)
                   AND location ILIKE :location
                   ORDER BY similarity(title, :title) DESC
                   LIMIT :limit OFFSET :offset
                   """)
        result = session.execute(
            sql,
            {
                "title": title,
                "location": f"%{city}%",
                "limit": fetch_limit,
                "offset": offset,
                "title_pattern": f"%{title}%",
            },
        )
        jobs = [Job(**dict(row._mapping)) for row in result]

    elif title:
        sql = text("""
               SELECT * FROM job
                WHERE (similarity(title, :title) > 0.1 OR title ILIKE :title_pattern)
                ORDER BY similarity(title, :title) DESC
                LIMIT :limit OFFSET :offset
               """)
        result = session.execute(
            sql,
            {
                "title": title,
                "limit": fetch_limit,
                "offset": offset,
                "title_pattern": f"%{title}%",
            },
        )
        jobs = [Job(**dict(row._mapping)) for row in result]

    elif city:
        query = query.where(Job.location.ilike(f"%{city}%"))
        jobs = session.exec(query.offset(offset).limit(fetch_limit)).all()

    else:
        jobs = session.exec(query.offset(offset).limit(fetch_limit)).all()

    return jobs


def get_featured_cities(session: Session):
    budva_jobs = session.exec(
        select(func.count()).select_from(Job).where(Job.location.ilike("%Budva%"))
    ).one()
    podgorica_jobs = session.exec(
        select(func.count()).select_from(Job).where(Job.location.ilike("%Podgorica%"))
    ).one()
    tivat_jobs = session.exec(
        select(func.count()).select_from(Job).where(Job.location.ilike("%Tivat%"))
    ).one()
    herceg_novi_jobs = session.exec(
        select(func.count()).select_from(Job).where(Job.location.ilike("%Herceg Novi%"))
    ).one()
    kotor_jobs = session.exec(
        select(func.count()).select_from(Job).where(Job.location.ilike("%Kotor%"))
    ).one()

    cities = [
        {
            "title": "Podgorica",
            "total_jobs": podgorica_jobs,
            "image": "images/cities/podgorica.jpg",
        },
        {
            "title": "Budva",
            "total_jobs": budva_jobs,
            "image": "images/cities/budva.webp",
        },
        {
            "title": "Herceg Novi",
            "total_jobs": herceg_novi_jobs,
            "image": "images/cities/herceg-novi.jpg",
        },
        {
            "title": "Tivat",
            "total_jobs": tivat_jobs,
            "image": "images/cities/tivat.avif",
        },
        {
            "title": "Kotor",
            "total_jobs": kotor_jobs,
            "image": "images/cities/kotor.jpg",
        },
    ]
    return cities


def get_featured_jobs(session: Session):
    featured_jobs = session.exec(
        select(Job)
        .where(Job.img.is_not(None), Job.img != "")
        .order_by(func.random())
        .limit(6)
    ).all()

    return featured_jobs
