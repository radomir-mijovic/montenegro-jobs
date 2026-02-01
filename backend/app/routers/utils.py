from app.models.job import Category, CategoryJobLink, Job
from app.redis_app import get_jobs_cache, set_jobs_cache
from app.scrapers.base import Job as JobBase
from sqlalchemy import ScalarResult, text
from sqlalchemy.sql import func
from sqlmodel import Session, select


def get_queried_jobs(
    *,
    title: str | None = None,
    city: str | None = None,
    category: str | None = None,
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

    elif category:
        query = (
            select(Job)
            .join(CategoryJobLink)
            .join(Category)
            .where(Category.name.ilike(f"%{category}"))
        )
        jobs = session.exec(query).all()

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


def get_cached_jobs(session: Session):
    cached_jobs = get_jobs_cache()
    if cached_jobs:
        return cached_jobs

    all_jobs = session.exec(select(Job)).all()
    pydantic_jobs = [JobBase.model_validate(job) for job in all_jobs]
    set_jobs_cache(pydantic_jobs)

    return pydantic_jobs


def get_jobs_count_based_on_category(name: str, session: Session) -> int:
    query = (
        select(func.count(Job.id))
        .join(CategoryJobLink)
        .join(Category)
        .where(Category.name == name)
    )
    return session.exec(query).one()


def get_category_name(name: str, session: Session) -> str | None:
    category_name = session.exec(
        select(Category).where(Category.name.ilike(f"%{name}%"))
    ).first()
    if category_name:
        return category_name.name

    return None


def get_categories(session: Session) -> list[dict]:
    categories_to_display: dict[str, str] = {
        "Ugostiteljstvo I Turizam": "tree-of-love",
        "Prodaja I Maloprodaja": "home",
        "Vožnja, Transport I Logistika": "car",
        "Obrazovanje": "notebook",
        "Zdravstvo I Medicina": "first-aid-kit-1",
        "Usluge I Zanatstvo": "maintenance",
        "Korisnička podrška": "support",
        "Proizvodnja I Industrija": "production",
        "Menadžment I Liderstvo": "handshake",
    }
    categories: list[dict] = []

    for name, icon in categories_to_display.items():
        cat_dict: dict = {}
        category_name = get_category_name(name, session=session)
        jobs_count = get_jobs_count_based_on_category(name, session=session)

        cat_dict["name"] = category_name
        cat_dict["count"] = jobs_count
        cat_dict["icon"] = icon

        categories.append(cat_dict)

    return categories
