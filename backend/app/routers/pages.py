from app.db import get_session
from app.models.job import Job
from app.routers.utils import get_featured_cities, get_featured_jobs, get_queried_jobs
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
    featured_jobs = get_featured_jobs(session=session)
    total = session.exec(select(func.count()).select_from(Job)).one()

    context = {
        "jobs": jobs,
        "total": total,
        "cities": cities,
        "featured_jobs": featured_jobs,
    }
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


@router.get("/sitemap.xml")
def sitemap(session: Session = Depends(get_session)):
    """Generate XML sitemap for search engines"""
    from datetime import datetime

    # Get all unique cities
    cities_result = session.exec(
        select(Job.location).distinct().where(Job.location.is_not(None))
    ).all()

    # Build sitemap XML
    urls = []
    base_url = "https://posaohub.me"
    today = datetime.now().strftime("%Y-%m-%d")

    # Homepage - highest priority
    urls.append(f"""
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>""")

    # Job search page
    urls.append(f"""
    <url>
        <loc>{base_url}/job-search</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>""")

    # City-specific job search pages
    for city in cities_result:
        if city:
            city_clean = city.strip()
            urls.append(f"""
    <url>
        <loc>{base_url}/job-search?city={city_clean}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>""")

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {''.join(urls)}
</urlset>"""

    return Response(content=sitemap_xml, media_type="application/xml")


@router.get("/robots.txt")
def robots():
    """Serve robots.txt"""
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://posaohub.me/sitemap.xml

Crawl-delay: 1"""
    return Response(content=content, media_type="text/plain")
