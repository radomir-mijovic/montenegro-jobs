import logging
from typing import List

from bs4 import BeautifulSoup

from .base import BaseScraper, Job

logger = logging.getLogger(__name__)


class PrekoVeze(BaseScraper):
    BASE_URL = "https://prekoveze.me/"

    def _build_url(self, page: int) -> str:
        params: str = f"oglasi-za-posao?page={page}"
        return self.BASE_URL + params

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.find_all("section", class_="job featured featured-primary mb-md")

        for card in job_cards:
            try:
                job = self._parse_job_details(card=card)
                jobs.append(job)

            except Exception as e:
                logger.warning(f"Error parsing job: {e}")
                continue

        return jobs

    def _parse_job_details(self, card) -> Job:
        title_elem = card.find("a")
        title = title_elem.get_text(strip=True) if title_elem else "N/A"

        url_elem = card.find("a")["href"]
        url = self.BASE_URL + url_elem if url_elem else self.BASE_URL

        img = card.find("img", class_="img-fluid")["src"]

        items = card.find("p")
        location = items.contents[0].strip() if items else "N/A"
        company = items.find("strong").get_text(strip=True) if items else "N/A"
        expires = items.find("span", class_="text-muted").get_text(strip=True) if items else "N/A"
        

        return Job(
            title=title,
            company=company,
            url=url,
            location=location,
            expires=expires,
            source="prekoveze.me",
            img=img,
        )
