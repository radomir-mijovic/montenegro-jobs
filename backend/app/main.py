import logging
import os
from contextlib import asynccontextmanager

from app.routers import pages
from app.tasks import create_all_categories_in_db, scrape_all_jobs
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    # Database schema is managed by Alembic migrations
    # Run: alembic upgrade head

    if os.environ.get("SCRAPE_ON_INITIAL"):
        logger.info("Inital scrape started")
        scrape_all_jobs.delay()

    if os.environ.get("CREATE_CATEGORIES_ON_INITIAL"):
        logger.info("Inital category creation started")
        create_all_categories_in_db()

    if os.environ.get("ASSIGN_CATEGORIES_ON_INITIAL"):
        logger.info("Inital category assign started")
        # assign_categories_to_jobs()

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
