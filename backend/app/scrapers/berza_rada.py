import logging
from typing import List

from app.scrapers.base import BaseScraper, Job
from app.scrapers.utils import convert_date
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BerzaRada(BaseScraper):
    BASE_URL = "https://www.berzarada.me"

    def _build_url(self, page: int) -> str:
        params: str = f"/poslovi/?p={page}"
        return self.BASE_URL + params

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        soup = BeautifulSoup(html, "html.parser")
        jobs_cards = soup.find_all("a", class_="job")

        for card in jobs_cards:
            try:
                job = self._parse_job_details(card)
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing job for berzarada: {e}")
                continue

        return jobs

    def _parse_job_details(self, card) -> Job:
        title_elem = card.find("h2")
        title = title_elem.get_text(strip=True)

        company_elem = card.find("div", class_="job-company").find_next("p")
        company = company_elem.get_text(strip=True)

        url = card["href"]

        img = card.find("img")["src"]

        location_elem = card.find("div", class_="location")
        location = location_elem.get_text(strip=True) if location_elem else "N/A"

        expires_elem = card.find("div", class_="job-title small-heading").find_next(
            "span"
        )
        expires = expires_elem.get_text(strip=True) if expires_elem else "N/A"
        expires_date_object = convert_date(expires)

        return Job(
            title=title,
            company=company,
            url=url,
            location=location,
            date_posted=None,
            expires=expires_date_object,
            source="berzarada.me",
            img=img,
        )
