# API Documentation

Complete API reference for PosaoHub Montenegro Jobs platform.

## Base URL

```
Development: http://localhost:8000
Production: https://posaohub.me
```

## Authentication

Currently, the API does not require authentication for public endpoints. Future versions may include API keys for scraping triggers and admin operations.

## Endpoints

### Health Check

Check if the API is running and healthy.

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy"
}
```

**Status Codes**:
- `200 OK`: Service is healthy

**Example**:
```bash
curl http://localhost:8000/api/health
```

---

### Root Endpoint

Welcome message and API information.

**Endpoint**: `GET /`

**Response**:
```json
{
  "message": "Welcome to Montenegro Jobs API"
}
```

**Status Codes**:
- `200 OK`: Success

---

## Web Pages

### Home Page

Display the main landing page with featured jobs and cities.

**Endpoint**: `GET /`

**Query Parameters**:
None

**Response**: HTML page

**Features**:
- Featured job listings
- Popular cities
- Search bar
- Job categories

---

### Job Search

Advanced job search and filtering.

**Endpoint**: `GET /job-search`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keyword` | string | No | Search term for job title or description |
| `location` | string | No | Job location filter |
| `category` | string | No | Job category filter |
| `employment_type` | string | No | Employment type (Full-time, Part-time, etc.) |
| `page` | integer | No | Page number for pagination (default: 1) |
| `per_page` | integer | No | Results per page (default: 20, max: 100) |

**Response**: HTML page with job results

**Example**:
```bash
# Search for developer jobs in Podgorica
curl "http://localhost:8000/job-search?keyword=developer&location=Podgorica"
```

**HTMX Integration**:
The job search page uses HTMX for dynamic loading:
- Results load without full page refresh
- Infinite scroll support
- Real-time filtering

---

## Data Models

### Job

```json
{
  "id": 1,
  "title": "Senior Software Developer",
  "company": "Tech Company",
  "location": "Podgorica",
  "employment_type": "Full-time",
  "category": "IT",
  "description": "We are looking for...",
  "url": "https://source.com/job/123",
  "source": "prekoveze",
  "posted_date": "2026-01-20T10:00:00Z",
  "expires": "2026-02-20T10:00:00Z",
  "created_at": "2026-01-20T10:05:00Z",
  "updated_at": "2026-01-20T10:05:00Z"
}
```

**Fields**:
- `id` (integer): Unique job identifier
- `title` (string): Job title
- `company` (string): Company name
- `location` (string): Job location
- `employment_type` (string): Type of employment
- `category` (string): Job category
- `description` (string): Job description
- `url` (string): Original job posting URL
- `source` (string): Job board source
- `posted_date` (datetime): When job was posted
- `expires` (datetime, nullable): When job expires
- `created_at` (datetime): When added to database
- `updated_at` (datetime): Last update time

---

## Internal API (Admin/Tasks)

These endpoints are typically accessed internally by Celery tasks or admin tools.

### Trigger Job Scraping

Manually trigger job scraping for all sources.

**Endpoint**: `POST /api/admin/scrape` (Future implementation)

**Authentication**: API Key required

**Response**:
```json
{
  "status": "started",
  "task_id": "abc-123-def",
  "message": "Job scraping initiated"
}
```

**Example**:
```bash
# Using Celery directly
docker-compose exec backend python -c "from app.tasks import scrape_all_jobs; scrape_all_jobs.delay()"
```

---

## Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service temporarily unavailable |

---

## Rate Limiting

Currently, no rate limiting is enforced. Future versions will implement:

- **Public API**: 100 requests per minute per IP
- **Authenticated API**: 1000 requests per minute per API key

---

## Pagination

List endpoints support pagination using query parameters:

```
GET /api/jobs?page=2&per_page=20
```

**Pagination Response**:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

---

## Filtering

Jobs can be filtered using query parameters:

### By Location
```
GET /job-search?location=Podgorica
```

### By Category
```
GET /job-search?category=IT
```

### By Employment Type
```
GET /job-search?employment_type=Full-time
```

### Combined Filters
```
GET /job-search?location=Budva&category=Tourism&employment_type=Seasonal
```

---

## Sorting

Future implementation will support sorting:

```
GET /api/jobs?sort_by=posted_date&order=desc
```

**Sort Options**:
- `posted_date`: Sort by posting date
- `title`: Sort alphabetically by title
- `company`: Sort by company name
- `location`: Sort by location

**Order**:
- `asc`: Ascending order
- `desc`: Descending order (default)

---

## Search

Full-text search across job titles and descriptions:

```
GET /job-search?keyword=python+developer
```

**Search Features**:
- Partial word matching
- Case-insensitive
- Searches: title, description, company
- Cyrillic and Latin script support

---

## HTMX Integration

The API is designed to work seamlessly with HTMX for dynamic content loading.

### Example: Search Form

```html
<form hx-get="/job-search" hx-target="#results" hx-trigger="submit">
  <input type="text" name="keyword" placeholder="Search jobs">
  <button type="submit">Search</button>
</form>

<div id="results">
  <!-- Results loaded here -->
</div>
```

### Example: Infinite Scroll

```html
<div hx-get="/job-search?page=2"
     hx-trigger="revealed"
     hx-swap="afterend">
  <!-- Next page loads when scrolled into view -->
</div>
```

---

## WebSocket Support

Future versions may include WebSocket support for:
- Real-time job updates
- Live search results
- Notification system

---

## SDKs and Client Libraries

Currently, no official SDKs are available. The API uses standard REST conventions and can be accessed using any HTTP client.

### Python Example

```python
import requests

# Search for jobs
response = requests.get(
    "http://localhost:8000/job-search",
    params={
        "keyword": "developer",
        "location": "Podgorica"
    }
)
html = response.text
```

### JavaScript Example

```javascript
// Using Fetch API
fetch('/job-search?keyword=developer&location=Podgorica')
  .then(response => response.text())
  .then(html => {
    document.getElementById('results').innerHTML = html;
  });
```

### cURL Example

```bash
curl -X GET "http://localhost:8000/job-search?keyword=developer&location=Podgorica"
```

---

## Error Handling

### Network Errors

If the API is unavailable:
```json
{
  "status": "error",
  "message": "Service temporarily unavailable",
  "code": "SERVICE_UNAVAILABLE"
}
```

### Validation Errors

If parameters are invalid:
```json
{
  "status": "error",
  "message": "Invalid parameter",
  "code": "VALIDATION_ERROR",
  "details": {
    "page": "Must be a positive integer"
  }
}
```

---

## Versioning

Currently on version 1.0. Future API versions will be accessible via:

```
/api/v2/jobs
```

---

## CORS

CORS is enabled for all origins in development. Production should restrict to:

```python
allow_origins=["https://posaohub.me"]
```

---

## OpenAPI/Swagger Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Future Endpoints

### Planned Features

#### Job Details
```
GET /api/jobs/{id}
```

#### Create Job Alert
```
POST /api/alerts
```

#### User Authentication
```
POST /api/auth/register
POST /api/auth/login
```

#### Save Jobs
```
POST /api/jobs/{id}/save
GET /api/jobs/saved
```

#### Analytics
```
GET /api/stats/jobs
GET /api/stats/companies
```

---

## Support

For API support or feature requests:
- GitHub Issues: [repository-url]/issues
- Email: support@posaohub.me
