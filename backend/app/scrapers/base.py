import logging
import time
from abc import ABC, abstractmethod
from datetime import date
from typing import List

import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Job(BaseModel):
    id: int | None = None
    title: str
    company: str
    location: str
    url: str
    source: str
    date_posted: date | None
    expires: date | None
    img: str

    model_config = {"from_attributes": True}


class BaseScraper(ABC):
    BASE_URL: str

    def __init__(self, delay: float = 3.0) -> None:
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _fetch_page(self, url: str) -> str | None:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None

    @abstractmethod
    def _build_url(self, page: int) -> str:
        """Need to build and return BASE_URL + additional params"""
        pass

    @abstractmethod
    def _parse_listing(self, html: str) -> List[Job]:
        pass

    @abstractmethod
    def _parse_job_details(self, card) -> Job:
        """Parsing job details"""
        pass

    def scrape(self, max_pages: int = 1) -> List[Job] | None:
        jobs = []

        for page in range(max_pages + 1):
            logger.info(f"Scraping jobs for {self}")
            url = self._build_url(page)
            html = self._fetch_page(url)

            if not html:
                break

            page_jobs = self._parse_listing(html)
            jobs.extend(page_jobs)

            time.sleep(self.delay)

        return jobs
