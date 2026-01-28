# Scrapers Documentation

This document provides detailed information about the job scraping system.

## Overview

The application uses a modular scraping system to collect job listings from multiple Montenegrin job boards. Each scraper is implemented as a separate module that inherits from the `BaseScraper` class.

## Architecture

### Base Scraper

Located in `backend/app/scrapers/base.py`, the `BaseScraper` class provides:

- Common scraping utilities
- Request handling with retry logic
- Data validation using Pydantic models
- Error handling and logging

### Job Model

```python
class Job(BaseModel):
    title: str
    company: str
    location: str
    employment_type: str
    category: str
    description: str
    url: str
    source: str
    posted_date: datetime
    expires: datetime | None
```

## Implemented Scrapers

### 1. Prekoveze.me Scraper

**File**: `backend/app/scrapers/prekoveze.py`

**URL Pattern**: `https://prekoveze.me/poslovi?page={page}`

**Features**:
- Scrapes job listings from paginated results
- Extracts company, location, and employment type
- Parses posted dates in Serbian format
- Handles relative dates (e.g., "Pre 2 dana")

**Implementation Details**:
```python
class PrekovezeScraper(BaseScraper):
    SOURCE = "prekoveze"
    BASE_URL = "https://prekoveze.me"

    def scrape(self, max_pages: int = 20) -> list[Job]:
        # Scrapes up to max_pages pages
        # Returns list of Job objects
```

**Selectors**:
- Job cards: `.job-card` or similar
- Title: `.job-title`
- Company: `.company-name`
- Location: `.location`

### 2. Zaposlime.me Scraper

**File**: `backend/app/scrapers/zaposlime.py`

**URL Pattern**: `https://zaposlime.me/jobs?page={page}`

**Features**:
- Scrapes job listings from search results
- Handles multi-location jobs
- Parses Cyrillic text
- Extracts employment type and category

**Implementation Details**:
```python
class ZaposlimeScraper(BaseScraper):
    SOURCE = "zaposlime"
    BASE_URL = "https://zaposlime.me"

    def scrape(self, max_pages: int = 40) -> list[Job]:
        # Implementation
```

### 3. ZZZCG.me Scraper

**File**: `backend/app/scrapers/zzzcg.py`

**URL Pattern**: `https://zzzcg.me/poslovi?page={page}`

**Features**:
- Scrapes from national employment service
- Handles government job postings
- Extracts detailed job information

**Implementation Details**:
```python
class ZZZCGScraper(BaseScraper):
    SOURCE = "zzzcg"
    BASE_URL = "https://zzzcg.me"

    def scrape(self, max_pages: int = 70) -> list[Job]:
        # Implementation
```

## Scraping Workflow

### 1. Scheduled Execution

Celery Beat triggers scraping at:
- **08:00** - Morning scrape
- **12:00** - Noon scrape
- **17:00** - Afternoon scrape

### 2. Parallel Execution

All scrapers run in parallel using Celery groups:

```python
job = group(
    scrape_single_source.s(source, max_pages)
    for source, max_pages in SOURCES.items()
)
```

### 3. Data Processing

1. **Scraping**: Each scraper collects raw job data
2. **Validation**: Pydantic validates data against Job model
3. **Deduplication**: Check existing jobs by URL
4. **Storage**: Save new jobs to PostgreSQL
5. **Tracking**: Store URLs in Redis for cleanup

### 4. Cleanup

After all scrapers complete, the cleanup task:
1. Compares database URLs with Redis (current scrape)
2. Identifies expired jobs (not in current scrape)
3. Deletes expired jobs from database
4. Clears Redis for next run

## Adding a New Scraper

### Step 1: Create Scraper Class

Create a new file in `backend/app/scrapers/`:

```python
# backend/app/scrapers/newsite.py
from app.scrapers.base import BaseScraper, Job
from datetime import datetime
import requests
from bs4 import BeautifulSoup

class NewSiteScraper(BaseScraper):
    SOURCE = "newsite"
    BASE_URL = "https://newsite.com"

    def scrape(self, max_pages: int = 10) -> list[Job]:
        jobs = []

        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/jobs?page={page}"

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                job_cards = soup.find_all("div", class_="job-listing")

                if not job_cards:
                    break

                for card in job_cards:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

            except Exception as e:
                self.logger.error(f"Error scraping page {page}: {e}")
                continue

        return jobs

    def _parse_job_card(self, card) -> Job | None:
        try:
            title = card.find("h3", class_="title").text.strip()
            company = card.find("span", class_="company").text.strip()
            location = card.find("span", class_="location").text.strip()
            url = self.BASE_URL + card.find("a")["href"]

            return Job(
                title=title,
                company=company,
                location=location,
                employment_type="Full-time",  # Parse from page
                category="General",  # Parse from page
                description="",  # Can fetch from detail page
                url=url,
                source=self.SOURCE,
                posted_date=datetime.now(),
                expires=None
            )
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
```

### Step 2: Register Scraper

Update `backend/app/scrapers/__init__.py`:

```python
from app.scrapers.prekoveze import PrekovezeScraper
from app.scrapers.zaposlime import ZaposlimeScraper
from app.scrapers.zzzcg import ZZZCGScraper
from app.scrapers.newsite import NewSiteScraper  # Add this

SCRAPERS = {
    "prekoveze": PrekovezeScraper,
    "zaposlime": ZaposlimeScraper,
    "zzzcg": ZZZCGScraper,
    "newsite": NewSiteScraper,  # Add this
}

def get_scraper(scraper: str):
    return SCRAPERS[scraper]()
```

### Step 3: Add to Task Configuration

Update `backend/app/tasks.py`:

```python
SOURCES: dict[str, int | None] = {
    "prekoveze": 20,
    "zaposlime": 40,
    "zzzcg": 70,
    "newsite": 10,  # Add this with max pages
}
```

### Step 4: Test Your Scraper

```bash
# Test scraper manually
docker-compose exec backend python -c "
from app.scrapers.newsite import NewSiteScraper
scraper = NewSiteScraper()
jobs = scraper.scrape(max_pages=1)
print(f'Found {len(jobs)} jobs')
for job in jobs[:3]:
    print(f'{job.title} at {job.company}')
"
```

## Best Practices

### 1. Respect Rate Limits

- Add delays between requests
- Use `time.sleep()` or async delays
- Respect robots.txt

### 2. Error Handling

```python
try:
    # Scraping code
except requests.RequestException as e:
    self.logger.error(f"Network error: {e}")
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
finally:
    # Cleanup
```

### 3. Data Validation

Always validate scraped data:

```python
if not title or not company or not url:
    self.logger.warning("Missing required fields")
    return None
```

### 4. Logging

Use structured logging:

```python
self.logger.info(f"Scraped {len(jobs)} jobs from {self.SOURCE}")
self.logger.error(f"Failed to parse job card: {error_details}")
```

### 5. User-Agent

Use a descriptive user-agent:

```python
headers = {
    "User-Agent": "PosaoHub/1.0 (+https://posaohub.me; job-aggregator)"
}
```

## Troubleshooting

### Scraper Returns No Jobs

1. Check if website structure changed
2. Verify selectors in browser DevTools
3. Check for rate limiting or blocking
4. Review logs for errors

### Data Quality Issues

1. Validate data after scraping
2. Add data cleaning functions
3. Handle encoding issues (Cyrillic text)
4. Normalize date formats

### Performance Issues

1. Reduce `max_pages` for testing
2. Add caching for duplicate requests
3. Use connection pooling
4. Implement async scraping

## Monitoring

### Scraper Metrics

Track these metrics:
- Jobs scraped per run
- Success/failure rate
- Scraping duration
- Error types and frequency

### Logs to Monitor

```bash
# Watch scraper activity
docker-compose logs -f celery_worker | grep scrape

# Check for errors
docker-compose logs celery_worker | grep ERROR

# View specific scraper
docker-compose logs celery_worker | grep prekoveze
```

## Legal Considerations

1. **Terms of Service**: Review each site's ToS
2. **Robots.txt**: Respect crawling rules
3. **Rate Limiting**: Don't overload servers
4. **Attribution**: Credit job sources
5. **Copyright**: Don't copy full descriptions without permission

## Future Improvements

- [ ] Add scraper health monitoring
- [ ] Implement proxy rotation
- [ ] Add JavaScript-rendered page support (Selenium/Playwright)
- [ ] Create scraper configuration UI
- [ ] Add data quality scoring
- [ ] Implement incremental scraping (delta updates)
- [ ] Add support for job detail page scraping
- [ ] Create scraper testing framework
