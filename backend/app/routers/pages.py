from app.db import get_session
from app.models.job import Job
from app.routers.utils import get_featured_cities, get_queried_jobs
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2.environment import TemplateModule
from sqlalchemy.sql import func
from sqlmodel import Session, select

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def root(request: Request, session: Session = Depends(get_session)):
    jobs = session.exec(
        select(Job)
        .where(Job.img.is_not(None), Job.img != "")
        .order_by(func.random())
        .limit(3)
    ).all()

    cities = get_featured_cities(session=session)
    total = session.exec(select(func.count()).select_from(Job)).one()

    context = {"jobs": jobs, "total": total, "cities": cities}
    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


@router.get("/job-search", response_class=HTMLResponse)
def job_search(
    request: Request,
    session: Session = Depends(get_session),
    limit: int = 10,
    title: str | None = None,
    city: str | None = None,
):
    jobs = get_queried_jobs(title=title, city=city, limit=limit, session=session)
    has_more = len(jobs) > limit

    if has_more:
        jobs = jobs[:limit]

    return templates.TemplateResponse(
        request=request,
        name="job-search.html",
        context={
            "jobs": jobs,
            "title": title or "",
            "city": city or "",
            "has_search": bool(title or city),
            "has_more": has_more,
        },
    )


@router.get("/job-query", response_class=HTMLResponse)
def job_query(
    request: Request,
    title: str | None = None,
    city: str | None = None,
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    if request.headers.get("HX-Request") != "true":
        return RedirectResponse("/job-search", status_code=303)

    jobs = get_queried_jobs(
        title=title, city=city, limit=limit, offset=offset, session=session
    )
    has_more = len(jobs) > limit

    if has_more:
        jobs = jobs[:limit]

    return templates.TemplateResponse(
        request=request,
        name="partials/job-result.html",
        context={"jobs": jobs, "has_more": has_more},
    )
