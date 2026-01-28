# Quick Start Guide

Get PosaoHub up and running in 5 minutes!

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually included with Docker Desktop)

## Setup Steps

### 1. Get the Code

```bash
git clone <repository-url>
cd montenegro-jobs
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
cd ..
```

The default values in `.env` work for local development!

### 3. Start Everything

```bash
docker-compose up --build
```

Wait for all services to start (about 1-2 minutes first time).

### 4. Access the Application

Open your browser and visit:

**🌐 http://localhost**

That's it! The application is running and scraping jobs.

## What's Running?

- **Web Application**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## See It in Action

### View Jobs

1. Go to http://localhost
2. Click "Find Jobs" or use search bar
3. Browse available jobs

### Search Jobs

Try searching:
- By keyword: "developer", "manager", "waiter"
- By location: "Podgorica", "Budva", "Tivat"
- By category: "IT", "Tourism", "Sales"

### Watch Scraping

```bash
# See scraping logs in real-time
docker-compose logs -f celery_worker
```

Jobs are automatically scraped at 8:00, 12:00, and 17:00 daily.

## Common Commands

```bash
# Stop everything
docker-compose down

# Start again
docker-compose up

# View logs
docker-compose logs -f

# Trigger manual scrape
docker-compose exec backend python -c "from app.tasks import scrape_all_jobs; scrape_all_jobs.delay()"

# Access database
docker-compose exec postgres psql -U postgres -d montenegro_jobs
```

## Troubleshooting

### Port Already in Use

If port 80 is already in use:

Edit `docker-compose.yml` and change:
```yaml
nginx:
  ports:
    - "8080:80"  # Changed from 80:80
```

Then access at http://localhost:8080

### Containers Won't Start

```bash
# Clean up and try again
docker-compose down -v
docker-compose up --build
```

### No Jobs Showing

Wait a few minutes for initial scraping to complete, or trigger manually:

```bash
docker-compose exec backend python -c "from app.tasks import scrape_all_jobs; scrape_all_jobs.delay()"
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check [API Documentation](docs/API.md) for API details
- See [Development Guide](docs/DEVELOPMENT.md) to contribute
- Review [Deployment Guide](docs/DEPLOYMENT.md) for production setup

## Need Help?

- Check the [documentation](./docs/)
- Open an [issue](https://github.com/your-repo/issues)
- Read the [FAQ](#faq) below

## FAQ

**Q: How often are jobs updated?**
A: Jobs are scraped automatically at 8:00, 12:00, and 17:00 every day.

**Q: Can I add more job sources?**
A: Yes! See the [Scrapers Documentation](docs/SCRAPERS.md) for how to add new sources.

**Q: Where is the data stored?**
A: In PostgreSQL database. Data persists in Docker volumes.

**Q: How do I reset everything?**
A: Run `docker-compose down -v` to remove all data and start fresh.

**Q: Can I run this without Docker?**
A: Yes, see the [Development Guide](docs/DEVELOPMENT.md) for local setup instructions.

## Quick Reference

### Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

### Docker Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Access container shell
docker-compose exec [service-name] bash

# Rebuild containers
docker-compose up --build
```

### Database Commands

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d montenegro_jobs

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Backup database
docker-compose exec postgres pg_dump -U postgres montenegro_jobs > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U postgres montenegro_jobs
```

Happy job hunting! 🎉
