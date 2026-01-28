# Deployment Guide

Complete guide for deploying PosaoHub to production on Hetzner VPS or other hosting providers.

## Prerequisites

- A VPS or dedicated server (recommended: 2+ CPU cores, 4GB+ RAM)
- Ubuntu 22.04 LTS or similar Linux distribution
- Domain name with DNS access
- SSH access to the server

## Step 1: Server Setup

### 1.1 Initial Server Configuration

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget nginx certbot python3-certbot-nginx

# Create a non-root user (if not exists)
sudo adduser deploy
sudo usermod -aG sudo deploy

# Switch to deploy user
su - deploy
```

### 1.2 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
su - deploy
```

## Step 2: Domain Configuration

### 2.1 Configure DNS Records

In your domain registrar (e.g., Namecheap):

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | Automatic |
| A | www | YOUR_SERVER_IP | Automatic |

Wait for DNS propagation (5-30 minutes).

### 2.2 Verify DNS

```bash
# Check DNS resolution
dig +short yourdomain.com
dig +short www.yourdomain.com
```

## Step 3: Application Deployment

### 3.1 Clone Repository

```bash
cd ~
git clone <your-repository-url> montenegro-jobs
cd montenegro-jobs
```

### 3.2 Configure Environment Variables

Create production environment file:

```bash
cd backend
cp .env.example .env
nano .env
```

Update with production values:

```bash
# Database
DATABASE_URL=postgresql://posaohub_user:SECURE_PASSWORD_HERE@postgres:5432/posaohub_db

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Optional: Monitoring
# SENTRY_DSN=your-sentry-dsn
```

**Security Note**: Use strong, unique passwords for production!

### 3.3 Update Docker Compose for Production

Edit `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: posaohub-postgres
    restart: always  # Add restart policy
    environment:
      - POSTGRES_DB=posaohub_db
      - POSTGRES_USER=posaohub_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # Use env file
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Remove exposed ports for security
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U posaohub_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: posaohub-redis
    restart: always
    volumes:
      - redis_data:/data
    # Remove exposed ports
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: posaohub-backend
    restart: always
    # Remove exposed port (Nginx will proxy)
    volumes:
      - ./backend:/code
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  celery_worker:
    build: ./backend
    container_name: posaohub-celery-worker
    restart: always
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - ./backend:/code
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  celery_beat:
    build: ./backend
    container_name: posaohub-celery-beat
    restart: always
    command: celery -A app.celery_app beat --loglevel=info
    volumes:
      - ./backend:/code
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  nginx:
    build: ./nginx
    container_name: posaohub-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL certificates
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 3.4 Configure Nginx

Update `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    upstream backend {
        server backend:8000;
    }

    # HTTP server (redirect to HTTPS)
    server {
        listen 80;
        server_name posaohub.me www.posaohub.me;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name posaohub.me www.posaohub.me;

        ssl_certificate /etc/letsencrypt/live/posaohub.me/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/posaohub.me/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Static files
        location /static/ {
            alias /code/app/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Application
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 90;
        }
    }
}
```

## Step 4: SSL Certificate Setup

### 4.1 Obtain SSL Certificate

```bash
# Stop nginx if running
sudo systemctl stop nginx

# Get certificate using Certbot
sudo certbot certonly --standalone -d posaohub.me -d www.posaohub.me

# Follow prompts and enter your email
```

### 4.2 Configure Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
# Verify with:
sudo systemctl list-timers | grep certbot
```

## Step 5: Build and Start Application

```bash
cd ~/montenegro-jobs

# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 6: Database Initialization

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify database
docker-compose exec postgres psql -U posaohub_user -d posaohub_db -c "\dt"
```

## Step 7: Verify Deployment

### 7.1 Health Checks

```bash
# Check backend health
curl https://posaohub.me/api/health

# Check if scraping is running
docker-compose logs celery_beat | tail -20
docker-compose logs celery_worker | tail -20
```

### 7.2 Test Application

1. Visit https://posaohub.me in browser
2. Verify SSL certificate (should show secure)
3. Test job search functionality
4. Check that jobs are being scraped

## Step 8: Monitoring Setup

### 8.1 Setup Log Rotation

Create `/etc/logrotate.d/montenegro-jobs`:

```
/var/log/montenegro-jobs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        docker-compose -f /home/deploy/montenegro-jobs/docker-compose.yml restart nginx
    endscript
}
```

### 8.2 Setup Monitoring (Optional)

```bash
# Install monitoring tools
docker run -d \
  --name=prometheus \
  --restart=always \
  -p 9090:9090 \
  prom/prometheus

docker run -d \
  --name=grafana \
  --restart=always \
  -p 3000:3000 \
  grafana/grafana
```

## Step 9: Backup Configuration

### 9.1 Database Backups

Create backup script `/home/deploy/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/posaohub_backup_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose -f /home/deploy/montenegro-jobs/docker-compose.yml \
  exec -T postgres pg_dump -U posaohub_user posaohub_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Make executable and setup cron:

```bash
chmod +x /home/deploy/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /home/deploy/backup.sh >> /var/log/backup.log 2>&1
```

### 9.2 Restore from Backup

```bash
# Stop application
cd ~/montenegro-jobs
docker-compose down

# Restore database
gunzip < /home/deploy/backups/posaohub_backup_TIMESTAMP.sql.gz | \
  docker-compose exec -T postgres psql -U posaohub_user posaohub_db

# Restart application
docker-compose up -d
```

## Step 10: Maintenance

### Update Application

```bash
cd ~/montenegro-jobs

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart celery_worker
```

## Troubleshooting

### Application Not Accessible

```bash
# Check if containers are running
docker-compose ps

# Check nginx logs
docker-compose logs nginx

# Check backend logs
docker-compose logs backend

# Verify DNS
dig +short posaohub.me
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Test certificate
openssl s_client -connect posaohub.me:443 -servername posaohub.me
```

### Database Connection Issues

```bash
# Check database status
docker-compose exec postgres pg_isready

# Connect to database
docker-compose exec postgres psql -U posaohub_user -d posaohub_db

# Check connections
docker-compose exec postgres psql -U posaohub_user -d posaohub_db \
  -c "SELECT * FROM pg_stat_activity;"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Restart services
docker-compose restart

# Optimize PostgreSQL if needed
docker-compose exec postgres psql -U posaohub_user -d posaohub_db \
  -c "VACUUM ANALYZE;"
```

## Security Checklist

- [ ] Strong passwords for database
- [ ] SSL certificate installed and auto-renewing
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] SSH key-based authentication enabled
- [ ] Regular security updates applied
- [ ] Database not exposed publicly
- [ ] Redis not exposed publicly
- [ ] Application logs rotated
- [ ] Backups automated and tested
- [ ] Monitoring configured

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_category ON jobs(category);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_source ON jobs(source);
```

### 2. Nginx Caching

Add to nginx.conf:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m max_size=1g inactive=60m;

location / {
    proxy_cache app_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_bypass $http_cache_control;
}
```

### 3. Redis Optimization

Update redis configuration for persistence:

```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## Scaling Considerations

### Horizontal Scaling

To scale Celery workers:

```bash
docker-compose up -d --scale celery_worker=3
```

### Vertical Scaling

Upgrade server resources:
- 4GB RAM → 8GB RAM
- 2 CPU cores → 4 CPU cores

## Support

For deployment issues:
- Check logs: `docker-compose logs`
- GitHub Issues: [repository-url]/issues
- Email: support@posaohub.me
