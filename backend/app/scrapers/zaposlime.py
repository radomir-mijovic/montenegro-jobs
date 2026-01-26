import logging
from typing import List

import requests
from bs4 import BeautifulSoup

from app.scrapers.utils import convert_date

from .base import BaseScraper, Job

logger = logging.getLogger(__name__)


class ZaposliMe(BaseScraper):
    BASE_URL = "https://zaposli.me/"

    def _build_url(self, page: int) -> str:
        params: str = f"oglasi-za-posao?page={page}"
        return self.BASE_URL + params

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.find_all(
            "div", class_="d-flex align-items-center justify-content-between"
        )

        for card in job_cards:
            try:
                job = self._parse_job_details(card)
                jobs.append(job)

            except Exception as e:
                logger.warning(f"Error parsing job: {e}")
                continue

        return jobs

    def _parse_job_details(self, card) -> Job:
        title_elem = card.find("h3", class_="text-primary-hover")
        title = title_elem.get_text(strip=True) if title_elem else "N/A"

        company_elem = card.find("h6")
        company = company_elem.get_text(strip=True) if company_elem else "N/A"

        url_elem = card.find("a")["href"]
        url = self.BASE_URL + url_elem if url_elem else "N/A"

        img = card.find("img", class_="rounded img-4by3-lg")["src"]

        items = card.find_all("li", class_="list-inline-item")
        location = items[1].get_text(strip=True) if items else "N/A"
        date_posted = items[0].get_text(strip=True) if items else None

        if date_posted:
            date_posted_object = convert_date(date_posted)
        else:
            date_posted_object = None

        detail_html = requests.get(url).text
        detail_soup = BeautifulSoup(detail_html, "html.parser")

        expires_elem = detail_soup.find("span", class_="ms-4").find_next("span")
        expires = expires_elem.get_text(strip=True)
        expires_date_object = convert_date(expires)

        return Job(
            title=title,
            company=company,
            url=url,
            location=location,
            date_posted=date_posted_object,
            expires=expires_date_object,
            source="zaposli.me",
            img=img,
        )
