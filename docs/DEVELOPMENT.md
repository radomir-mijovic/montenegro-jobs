# Development Guide

Complete guide for setting up and contributing to PosaoHub development.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Common Tasks](#common-tasks)

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- Code editor (VS Code recommended)

### Initial Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd montenegro-jobs
```

2. **Start development environment**

```bash
docker-compose up --build
```

3. **Access the application**

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Environment

### Docker Development

The project uses Docker for development consistency.

**Services**:
- `backend`: FastAPI application
- `postgres`: PostgreSQL database
- `redis`: Redis cache & message broker
- `celery_worker`: Background task processor
- `celery_beat`: Task scheduler
- `nginx`: Reverse proxy

**Volumes**:
- Backend code is mounted for hot reload
- Database persists in named volume

### Local Development (Without Docker)

If you prefer local development:

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
nano .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# In separate terminal, start Celery worker
celery -A app.celery_app worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.celery_app beat --loglevel=info
```

## Project Structure

```
montenegro-jobs/
├── backend/
│   ├── alembic/                  # Database migrations
│   │   ├── versions/             # Migration files
│   │   └── env.py                # Migration environment
│   ├── app/
│   │   ├── db/                   # Database configuration
│   │   │   ├── __init__.py
│   │   │   └── session.py        # DB session management
│   │   ├── models/               # SQLModel data models
│   │   │   ├── __init__.py
│   │   │   └── job.py            # Job model
│   │   ├── routers/              # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── pages.py          # Page routes
│   │   │   └── utils.py          # Router utilities
│   │   ├── scrapers/             # Web scraping modules
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base scraper class
│   │   │   ├── prekoveze.py
│   │   │   ├── zaposlime.py
│   │   │   ├── zzzcg.py
│   │   │   └── utils.py          # Scraper utilities
│   │   ├── static/               # Static assets
│   │   │   ├── css/
│   │   │   ├── js/
│   │   │   ├── images/
│   │   │   └── fonts/
│   │   ├── templates/            # Jinja2 templates
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── job-search.html
│   │   │   └── partials/
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── config.py             # Application config
│   │   ├── main.py               # FastAPI app
│   │   └── tasks.py              # Celery tasks
│   ├── Dockerfile                # Backend container
│   ├── entrypoint.sh             # Container entry point
│   └── requirements.txt          # Python dependencies
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf                # Nginx configuration
├── docs/                         # Documentation
│   ├── API.md
│   ├── SCRAPERS.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── docker-compose.yml            # Docker services
└── README.md                     # Project README
```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these tools:

```bash
# Install dev tools
pip install black isort flake8 ruff

# Format code with Black
black backend/app

# Sort imports with isort
isort backend/app

# Lint with Flake8
flake8 backend/app

# Or use Ruff (faster)
ruff check backend/app
ruff format backend/app
```

### Code Formatting

**Black Configuration** (pyproject.toml):

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.ruff]
line-length = 88
target-version = "py311"
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Variables**: `snake_case`
- **Constants**: `UPPER_CASE`

### Code Organization

```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from fastapi import FastAPI
from sqlmodel import Session

# Local imports
from app.models import Job
from app.scrapers import get_scraper
```

### Type Hints

Use type hints for all functions:

```python
def get_jobs(
    session: Session,
    location: str | None = None,
    limit: int = 20
) -> list[Job]:
    """Get jobs with optional filtering."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def scrape_jobs(source: str, max_pages: int) -> list[Job]:
    """Scrape jobs from a specific source.

    Args:
        source: The job board to scrape (e.g., 'prekoveze')
        max_pages: Maximum number of pages to scrape

    Returns:
        List of Job objects

    Raises:
        ValueError: If source is not recognized
        RequestException: If scraping fails
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/test_scrapers.py

# Run specific test
docker-compose exec backend pytest tests/test_scrapers.py::test_prekoveze_scraper
```

### Writing Tests

Create tests in `backend/tests/`:

```python
# tests/test_scrapers.py
import pytest
from app.scrapers.prekoveze import PrekovezeScraper

def test_prekoveze_scraper():
    """Test Prekoveze scraper returns jobs."""
    scraper = PrekovezeScraper()
    jobs = scraper.scrape(max_pages=1)

    assert len(jobs) > 0
    assert jobs[0].title is not None
    assert jobs[0].company is not None

def test_prekoveze_scraper_with_invalid_page():
    """Test scraper handles invalid pages gracefully."""
    scraper = PrekovezeScraper()
    jobs = scraper.scrape(max_pages=999)

    # Should not crash, may return empty list
    assert isinstance(jobs, list)
```

### Test Coverage

Aim for 80%+ code coverage:

```bash
# Generate coverage report
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# View HTML report
docker-compose exec backend pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in browser
```

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation
- `test/description` - Tests

### Commit Messages

Follow Conventional Commits:

```
feat: add user authentication
fix: resolve database connection timeout
docs: update API documentation
refactor: simplify scraper logic
test: add tests for job model
chore: update dependencies
```

**Format**:
```
<type>: <description>

[optional body]

[optional footer]
```

### Pull Request Process

1. Create a feature branch:
```bash
git checkout -b feature/my-feature
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: add new feature"
```

3. Push to remote:
```bash
git push origin feature/my-feature
```

4. Create pull request on GitHub

5. Address review feedback

6. Merge after approval

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.log or debug code
- [ ] Type hints present
- [ ] Error handling implemented
- [ ] No hardcoded values
- [ ] Performance considered

## Common Tasks

### Adding a New API Endpoint

1. **Define route** in `app/routers/pages.py`:

```python
@router.get("/jobs/{job_id}")
async def get_job(job_id: int, session: Session = Depends(get_session)):
    """Get job by ID."""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

2. **Add tests**:

```python
def test_get_job(client):
    response = client.get("/jobs/1")
    assert response.status_code == 200
    assert "title" in response.json()
```

3. **Update API documentation** in `docs/API.md`

### Adding a New Database Model

1. **Create model** in `app/models/`:

```python
# app/models/company.py
from sqlmodel import SQLModel, Field
from datetime import datetime

class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    website: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
```

2. **Create migration**:

```bash
docker-compose exec backend alembic revision --autogenerate -m "add company model"
```

3. **Review migration** in `alembic/versions/`

4. **Apply migration**:

```bash
docker-compose exec backend alembic upgrade head
```

### Adding a New Scraper

See [SCRAPERS.md](./SCRAPERS.md) for detailed guide.

Quick steps:

1. Create scraper class in `app/scrapers/new_site.py`
2. Register in `app/scrapers/__init__.py`
3. Add to `SOURCES` in `app/tasks.py`
4. Test scraper
5. Add tests

### Modifying Templates

Templates use Jinja2 syntax:

```html
<!-- templates/job-card.html -->
<div class="job-card">
    <h3>{{ job.title }}</h3>
    <p>{{ job.company }}</p>

    {% if job.location %}
    <span>{{ job.location }}</span>
    {% endif %}
</div>
```

### Adding Celery Tasks

1. **Define task** in `app/tasks.py`:

```python
@celery_app.task(name="app.tasks.send_notification")
def send_notification(user_id: int, message: str):
    """Send notification to user."""
    # Implementation
    logger.info(f"Sending notification to user {user_id}")
```

2. **Schedule task** (if periodic):

```python
celery_app.conf.beat_schedule = {
    "send-daily-digest": {
        "task": "app.tasks.send_notification",
        "schedule": crontab(hour=8, minute=0),
    },
}
```

3. **Trigger manually**:

```python
send_notification.delay(user_id=1, message="Hello")
```

### Database Queries

Use SQLModel for queries:

```python
from sqlmodel import select, and_, or_

# Simple query
jobs = session.exec(select(Job).where(Job.location == "Podgorica")).all()

# Multiple conditions
jobs = session.exec(
    select(Job)
    .where(and_(
        Job.location == "Podgorica",
        Job.category == "IT"
    ))
    .limit(20)
).all()

# Order by
jobs = session.exec(
    select(Job)
    .order_by(Job.posted_date.desc())
    .limit(10)
).all()

# Count
count = session.exec(
    select(func.count(Job.id))
    .where(Job.location == "Podgorica")
).one()
```

## Debugging

### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--port", "8000"
            ],
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

### Debug Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy (VS Code)
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

## Performance Profiling

### Profile Endpoint

```bash
# Install profiler
pip install py-spy

# Profile application
py-spy top --pid $(pgrep -f uvicorn)

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f uvicorn)
```

### Database Query Profiling

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    print(f"Query took {total:.4f}s: {statement}")
```

## Resources

### Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLModel Docs](https://sqlmodel.tiangolo.com/)
- [Celery Docs](https://docs.celeryproject.org/)
- [Docker Docs](https://docs.docker.com/)

### Tools

- [Postman](https://www.postman.com/) - API testing
- [DBeaver](https://dbeaver.io/) - Database management
- [Redis Commander](https://github.com/joeferner/redis-commander) - Redis GUI

### Community

- GitHub Discussions
- Stack Overflow
- Discord/Slack channel (if available)

## Getting Help

1. Check documentation
2. Search existing issues
3. Ask in discussions
4. Create new issue with:
   - Description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Logs/screenshots

## Contributing

We welcome contributions! Please:

1. Read this guide thoroughly
2. Follow coding standards
3. Write tests
4. Update documentation
5. Submit pull request

Thank you for contributing to PosaoHub!
