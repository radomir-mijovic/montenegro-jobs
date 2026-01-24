# Montenegro Jobs

A full-stack job listing application built with FastAPI, Next.js, and Nginx in Docker.

## Project Structure

```
montenegro-jobs/
├── backend/           # FastAPI backend
│   ├── app/
│   │   └── main.py   # Main API endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── Dockerfile
│   ├── next.config.js
│   ├── package.json
│   └── tsconfig.json
├── nginx/             # Nginx reverse proxy
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + Next.js (TypeScript)
- **Proxy**: Nginx
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone or navigate to the project directory:
```bash
cd montenegro-jobs
```

2. Build and start all services:
```bash
docker-compose up --build
```

3. Access the application:
   - **Frontend**: http://localhost
   - **Backend API**: http://localhost/api
   - **Direct Backend**: http://localhost:8000
   - **Direct Frontend**: http://localhost:3000

## API Endpoints

- `GET /` - Welcome message
- `GET /api/health` - Health check
- `GET /api/jobs` - Get list of jobs

## Development

### Backend Development

The backend code is mounted as a volume, so changes to `/backend/app` will trigger auto-reload.

### Frontend Development

To enable hot-reload for frontend development, you may need to adjust the Dockerfile or run Next.js in development mode.

## Stopping the Application

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

## Architecture

The application uses Nginx as a reverse proxy:
- Requests to `/` are routed to the Next.js frontend
- Requests to `/api` are routed to the FastAPI backend
- All services communicate through a Docker network
