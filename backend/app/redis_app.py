import json
import os
from typing import List, Sequence

from app.scrapers.base import Job
from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis = Redis(
    host=REDIS_HOST,
    port=6379,
    password=REDIS_PASSWORD,
    decode_responses=True
)

JOB_CACHE_KEY: str = "list:jobs"
JOB_CACHE_TTL: int = 300


def set_jobs_cache(jobs: Sequence[Job]):
    redis.set(
        JOB_CACHE_KEY,
        json.dumps([job.model_dump(mode='json') for job in jobs]),
        ex=JOB_CACHE_TTL
    )


def get_jobs_cache() -> List[Job] | None:
    cached_jobs = redis.get(JOB_CACHE_KEY)
    if not cached_jobs:
        return None

    job_dicts = json.loads(cached_jobs)
    return [Job(**job_dict) for job_dict in job_dicts]
