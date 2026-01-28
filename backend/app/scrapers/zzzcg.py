import logging
from typing import List

from app.scrapers.utils import convert_date
from bs4 import BeautifulSoup

from .base import BaseScraper, Job, requests

logger = logging.getLogger(__name__)


class ZzzCg(BaseScraper):
    BASE_URL = "https://www.zzzcg.me/"

    def _build_url(self, page: int) -> str:
        params: str = f"srm/?e-page-740d986={page}"
        return self.BASE_URL + params

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.find_all(
            "div",
            class_="e-loop-item",
        )

        for card in job_cards:
            try:
                job: Job | None = self._parse_job_details(card=card)
                if job:
                    jobs.append(job)

            except Exception as e:
                logger.warning(f"Error parsing job for zzzcg: {e}")
                continue

        return jobs

    def _parse_job_details(self, card) -> Job | None:
        is_expired = card.find("div", class_="rokzaprijavujeistekao")

        if not is_expired:
            title_elem = card.find("h3", class_="elementor-heading-title")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            url = card.find("a", class_="elementor-element")["href"]

            items = card.find_all("li", class_="elementor-icon-list-item")
            company = items[0].get_text(strip=True) if items else "N/A"
            location = items[1].get_text(strip=True) if items else "N/A"
            date_posted = items[2].get_text(strip=True) if items else "N/A"
            date_posted_object = convert_date(date_posted, source="zzzcg")

            detail_html = requests.get(url).text
            detail_soup = BeautifulSoup(detail_html, "html.parser")

            expires_elem = detail_soup.select_one("div.rokzaprijavu")
            expires = expires_elem.get_text(strip=True) if expires_elem else "N/A"
            expires_str = expires.replace("Važi do:", "")
            expires_date_object = convert_date(expires_str, source="zzzcg")

            return Job(
                title=title,
                company=company,
                location=location,
                url=url,
                date_posted=date_posted_object,
                expires=expires_date_object,
                source="zzzcg.me",
                img="",
            )
