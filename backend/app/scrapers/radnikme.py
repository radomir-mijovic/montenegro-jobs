import logging
import time
from typing import List

from app.scrapers.base import BaseScraper, Job
from app.scrapers.utils import convert_date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class RadnikMe(BaseScraper):
    BASE_URL = "https://radnik.me"
    MAX_SCROLLS = 15

    def _build_url(self, page: int) -> str:
        return self.BASE_URL

    def _parse_listing(self, html: str) -> List[Job]:
        jobs: List = []
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Set a real user agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=options)

        # Hide webdriver property
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """},
        )

        try:
            driver.get(self.BASE_URL + "/oglasi-za-posao")
            time.sleep(5)  # Initial load - wait for JS to fully load

            no_change_count = 0

            for i in range(self.MAX_SCROLLS):
                # Count current job cards
                job_cards = driver.find_elements(By.CLASS_NAME, "job-item")
                current_job_count = len(job_cards)

                logger.info(
                    f"Scroll {i+1}/{self.MAX_SCROLLS}: {current_job_count} jobs loaded"
                )

                # Smooth scroll in steps to trigger intersection observer
                scroll_step = 300
                for _ in range(5):
                    driver.execute_script(f"window.scrollBy(0, {scroll_step});")
                    time.sleep(0.5)

                # Final scroll to absolute bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait longer for the loading dots to appear and disappear
                time.sleep(8)

                # Count jobs again after scroll
                job_cards_after = driver.find_elements(By.CLASS_NAME, "job-item")
                new_job_count = len(job_cards_after)

                logger.info(
                    f"After scroll: {new_job_count} jobs (gained {new_job_count - current_job_count})"
                )

                if new_job_count == current_job_count:
                    no_change_count += 1
                    # If job count hasn't changed 2 times in a row, we've reached the end
                    if no_change_count >= 2:
                        logger.info(f"Reached end of page. Total jobs: {new_job_count}")
                        break
                else:
                    no_change_count = 0

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            jobs_cards = soup.find_all("div", class_="job-item")

            for card in jobs_cards:
                job = self._parse_job_details(card)
                if job:
                    jobs.append(job)

            return jobs

        finally:
            driver.quit()

    def _parse_job_details(self, card) -> Job:
        title_elem = card.find("h3", class_="title")
        title = title_elem.get_text(strip=True)

        company_elem = card.find("div", class_="company-link")
        company = company_elem.get_text(strip=True)

        url_elem = card.find("a", class_="card job row")["href"]
        url = self.BASE_URL + url_elem if url_elem else "N/A"

        img = card.find("img", class_="image")["src"]

        items = card.find_all("div", class_="job-category-text")
        location = items[0].get_text(strip=True) if items else "N/A"

        detail_html = self.session.get(url, timeout=10).text
        detail_soup = BeautifulSoup(detail_html, "html.parser")

        expires_elem = detail_soup.find(string=lambda t: "Oglas je aktivan do" in t)
        expires = expires_elem.find_next("b").get_text(strip=True)
        expires_date_object = convert_date(expires)

        return Job(
            title=title,
            company=company,
            url=url,
            location=location,
            date_posted=None,
            expires=expires_date_object,
            source="radnik.me",
            img=img,
        )
