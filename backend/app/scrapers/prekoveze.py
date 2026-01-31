import logging
from typing import List

from app.scrapers.utils import convert_date
from bs4 import BeautifulSoup

from .base import BaseScraper, Job

logger = logging.getLogger(__name__)


class PrekoVeze(BaseScraper):
    BASE_URL = "https://prekoveze.me"

    def _build_url(self, page: int) -> str:
        params: str = f"/oglasi-za-posao?page={page}"
        return self.BASE_URL + params

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.find_all(
            "section", class_="job featured featured-primary mb-md"
        )

        for card in job_cards:
            try:
                job = self._parse_job_details(card=card)
                jobs.append(job)

            except Exception as e:
                logger.warning(f"Error parsing job for prekoveze: {e}")
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
        expires = (
            items.find("span", class_="text-muted").get_text(strip=True)
            if items
            else "N/A"
        )
        expires_str = expires.replace("Važi do: ", "")
        expires_date_object = convert_date(expires_str, source="prekoveze")

        return Job(
            title=title,
            company=company,
            url=url,
            location=location,
            date_posted=None,
            expires=expires_date_object,
            source="prekoveze.me",
            img=img,
        )

    def last_page_number(self) -> int | None:
        url = self.BASE_URL + "/oglasi-za-posao"
        html = self._fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        pagination_items = soup.find_all("a", class_="page-link")
        last_page_str = (
            pagination_items[-2].get_text(strip=True) if pagination_items else None
        )
        if last_page_str:
            return int(last_page_str)


_prekoveze = PrekoVeze()
last_page_number = _prekoveze.last_page_number()
