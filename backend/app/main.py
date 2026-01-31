import logging
from contextlib import asynccontextmanager

from app.routers import pages
from app.tasks import scrape_all_jobs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    # Database schema is managed by Alembic migrations
    # Run: alembic upgrade head

    scrape_all_jobs.delay()
    logger.info("Triggering inital scraping")

    yield
    logger.info("Shutting down application...")


app = FastAPI(title="Montenegro Jobs", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(pages.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to Montenegro Jobs API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
