# PosaoHub - Montenegro Jobs

A comprehensive job aggregation platform for Montenegro that scrapes and consolidates job listings from multiple sources into a single, easy-to-use interface.

## Features

- **Multi-Source Job Scraping**: Automatically scrapes jobs from multiple Montenegrin job boards (Prekoveze, Zaposlime, ZZZCG)
- **Scheduled Scraping**: Automated job updates at 8:00, 12:00, and 17:00 daily
- **Smart Data Management**: Automatic cleanup of expired job listings
- **Search & Filter**: Advanced job search with location, category, and keyword filters
- **Featured Content**: Highlights popular jobs and cities
- **SEO Optimized**: Comprehensive SEO implementation for better discoverability
- **Responsive Design**: Mobile-friendly interface with modern UI
- **Real-time Updates**: HTMX-powered dynamic content loading

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLModel**: SQL database ORM
- **PostgreSQL**: Primary database
- **Redis**: Caching and Celery message broker
- **Celery**: Distributed task queue for job scraping
- **BeautifulSoup4**: Web scraping library
- **Jinja2**: Template engine

### Frontend
- **HTMX**: Dynamic content loading
- **Bootstrap 5**: UI framework
- **jQuery**: DOM manipulation and AJAX

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy and static file serving
- **Alembic**: Database migrations

## Project Structure

```
montenegro-jobs/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── db/               # Database configuration
│   │   ├── models/           # SQLModel data models
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── scrapers/         # Job scraping modules
│   │   │   ├── base.py       # Base scraper class
│   │   │   ├── prekoveze.py  # Prekoveze.me scraper
│   │   │   ├── zaposlime.py  # Zaposlime.me scraper
│   │   │   └── zzzcg.py      # ZZZCG.me scraper
│   │   ├── static/           # CSS, JS, images
│   │   ├── templates/        # Jinja2 HTML templates
│   │   ├── celery_app.py     # Celery configuration
│   │   ├── config.py         # App configuration
│   │   ├── main.py           # FastAPI application
│   │   └── tasks.py          # Celery tasks
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd montenegro-jobs
```

### 2. Environment Configuration

Create a `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/montenegro_jobs

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Start the Application

```bash
docker-compose up --build
```

This will start all services:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost (via Nginx)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task scheduler

### 4. Initial Setup

On first startup, the application will:
1. Initialize the database schema
2. Trigger an initial job scraping run
3. Start scheduled scraping (8:00, 12:00, 17:00)

## Usage

### Web Interface

Visit http://localhost to:
- Browse all available jobs
- Search by keyword, location, or category
- View featured jobs and cities
- Filter by job type and employment type

### API Endpoints

- `GET /` - Home page
- `GET /job-search` - Job search page with filters
- `GET /api/health` - Health check endpoint

### Manual Job Scraping

To manually trigger job scraping:

```bash
docker-compose exec backend python -c "from app.tasks import scrape_all_jobs; scrape_all_jobs.delay()"
```

## Development

### Backend Development

The backend code is mounted as a volume, so changes will trigger auto-reload:

```bash
# Watch logs
docker-compose logs -f backend

# Access backend container
docker-compose exec backend bash

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Adding a New Scraper

1. Create a new scraper in `backend/app/scrapers/`:

```python
from app.scrapers.base import BaseScraper, Job

class NewSiteScraper(BaseScraper):
    SOURCE = "newsite"
    BASE_URL = "https://newsite.com"

    def scrape(self, max_pages: int = 10) -> list[Job]:
        # Implementation
        pass
```

2. Register it in `backend/app/scrapers/__init__.py`
3. Add to `SOURCES` in `backend/app/tasks.py`

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Celery Tasks

Monitor Celery tasks:

```bash
# View worker logs
docker-compose logs -f celery_worker

# View beat scheduler logs
docker-compose logs -f celery_beat
```

## Testing

```bash
# Run backend tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app
```

## Deployment

### Production Considerations

1. **Environment Variables**: Use secure credentials
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service or Redis Cluster
4. **SSL/TLS**: Configure Nginx with SSL certificates
5. **Monitoring**: Add application monitoring (e.g., Sentry)
6. **Scaling**: Scale Celery workers based on load

### Deploy to Hetzner

1. Set up a Hetzner VPS
2. Install Docker and Docker Compose
3. Configure domain DNS A records to point to server IP
4. Clone repository and configure environment
5. Set up SSL with Let's Encrypt:

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

6. Update `docker-compose.yml` for production:
   - Remove port mappings for internal services
   - Use environment files for secrets
   - Configure restart policies

### Environment Variables (Production)

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/0
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/api/health

# Check database connection
docker-compose exec postgres pg_isready

# Check Redis
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Celery Not Processing Tasks

```bash
# Check if worker is running
docker-compose ps celery_worker

# Restart worker
docker-compose restart celery_worker

# Check Redis connection
docker-compose exec celery_worker python -c "from app.celery_app import celery_app; print(celery_app.broker_connection().ensure_connection())"
```

### Scraping Issues

```bash
# Check scraper logs
docker-compose logs -f celery_worker | grep scrape

# Test a single scraper
docker-compose exec backend python -c "from app.scrapers import get_scraper; scraper = get_scraper('prekoveze'); jobs = scraper.scrape(max_pages=1); print(f'Found {len(jobs)} jobs')"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Job sources: Prekoveze.me, Zaposlime.me, ZZZCG.me
- UI Template: Superio

## Support

For issues and questions, please open an issue on the GitHub repository.
