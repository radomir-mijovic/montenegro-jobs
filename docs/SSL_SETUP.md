# SSL/HTTPS Certificate Setup Guide

Complete guide for adding HTTPS certificates to PosaoHub.

## Production Setup (Let's Encrypt - Recommended)

### Prerequisites

- Domain pointing to your server (A records configured)
- Server with ports 80 and 443 open
- Docker and Docker Compose installed

### Step 1: Install Certbot on Server

SSH into your server and run:

```bash
# Update packages
sudo apt update

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Stop Docker Nginx (if running)

```bash
cd ~/montenegro-jobs
docker-compose stop nginx
```

### Step 3: Obtain SSL Certificate

```bash
# Get certificate for your domain
sudo certbot certonly --standalone \
  -d posaohub.me \
  -d www.posaohub.me \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

**Follow the prompts:**
- Enter your email
- Agree to terms of service
- Choose whether to share email with EFF

Certificates will be saved to:
```
/etc/letsencrypt/live/posaohub.me/fullchain.pem
/etc/letsencrypt/live/posaohub.me/privkey.pem
```

### Step 4: Update Nginx Configuration

Create/update `nginx/nginx.conf`:

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

    upstream backend {
        server backend:8000;
    }

    # HTTP server - Redirect to HTTPS
    server {
        listen 80;
        server_name posaohub.me www.posaohub.me;

        # Allow Let's Encrypt verification
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all other traffic to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name posaohub.me www.posaohub.me;

        # SSL Certificate files
        ssl_certificate /etc/letsencrypt/live/posaohub.me/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/posaohub.me/privkey.pem;

        # SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Max upload size
        client_max_body_size 10M;

        # Static files
        location /static/ {
            alias /code/app/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Application
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 90;
        }
    }
}
```

### Step 5: Update Docker Compose

Update `docker-compose.yml` to mount SSL certificates:

```yaml
nginx:
  build: ./nginx
  container_name: montenegro-jobs-nginx
  restart: always
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro  # Add this line
    - /var/www/certbot:/var/www/certbot:ro  # Add this line
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - backend
  networks:
    - app-network
```

### Step 6: Restart Services

```bash
cd ~/montenegro-jobs
docker-compose up -d --build nginx
```

### Step 7: Verify HTTPS

Visit your site:
- https://posaohub.me
- https://www.posaohub.me

Check certificate:
```bash
# Test SSL certificate
openssl s_client -connect posaohub.me:443 -servername posaohub.me

# Check certificate expiry
echo | openssl s_client -servername posaohub.me -connect posaohub.me:443 2>/dev/null | openssl x509 -noout -dates
```

### Step 8: Setup Auto-Renewal

Let's Encrypt certificates expire after 90 days. Setup automatic renewal:

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Certbot automatically creates a systemd timer
# Verify it's active
sudo systemctl status certbot.timer
```

**Manual renewal if needed:**
```bash
sudo certbot renew
docker-compose restart nginx
```

**Create renewal hook** (optional):

Create `/etc/letsencrypt/renewal-hooks/post/reload-nginx.sh`:

```bash
#!/bin/bash
cd /home/deploy/montenegro-jobs
docker-compose restart nginx
```

Make it executable:
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

## Alternative: Using Certbot with Docker

If you prefer to keep everything in Docker:

### Step 1: Update docker-compose.yml

```yaml
services:
  certbot:
    image: certbot/certbot
    container_name: montenegro-jobs-certbot
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - /var/www/certbot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

  nginx:
    build: ./nginx
    container_name: montenegro-jobs-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - app-network
```

### Step 2: Initial Certificate Request

```bash
# Start services
docker-compose up -d

# Request certificate
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d posaohub.me \
  -d www.posaohub.me \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Restart nginx to load certificates
docker-compose restart nginx
```

## Local Development (Self-Signed Certificate)

For testing HTTPS locally:

### Step 1: Generate Self-Signed Certificate

```bash
# Create ssl directory
mkdir -p nginx/ssl

# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/localhost-key.pem \
  -out nginx/ssl/localhost-cert.pem \
  -subj "/C=ME/ST=Montenegro/L=Podgorica/O=PosaoHub/CN=localhost"
```

### Step 2: Update Local Nginx Config

Create `nginx/nginx.local.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream backend {
        server backend:8000;
    }

    # HTTP - redirect to HTTPS
    server {
        listen 80;
        server_name localhost;
        return 301 https://$host$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/localhost-cert.pem;
        ssl_certificate_key /etc/nginx/ssl/localhost-key.pem;

        location /static/ {
            alias /code/app/static/;
        }

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Step 3: Update Docker Compose for Local

```yaml
nginx:
  volumes:
    - ./nginx/ssl:/etc/nginx/ssl:ro
    - ./nginx/nginx.local.conf:/etc/nginx/nginx.conf:ro
```

### Step 4: Access Locally

Visit https://localhost (you'll see a security warning - click "Advanced" and proceed)

## Troubleshooting

### Certificate Not Loading

```bash
# Check certificate files exist
ls -la /etc/letsencrypt/live/posaohub.me/

# Check nginx can read certificates
docker-compose exec nginx ls -la /etc/letsencrypt/live/posaohub.me/

# Check nginx configuration
docker-compose exec nginx nginx -t

# View nginx logs
docker-compose logs nginx
```

### Port 443 Not Accessible

```bash
# Check firewall
sudo ufw status
sudo ufw allow 443/tcp

# Check if port is open
sudo netstat -tlnp | grep :443
```

### Certificate Renewal Failed

```bash
# Check certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log

# Manual renewal
sudo certbot renew --force-renewal

# Restart nginx
docker-compose restart nginx
```

### Mixed Content Warnings

If you see mixed content warnings, update your templates to use relative URLs or HTTPS:

```html
<!-- Bad -->
<img src="http://posaohub.me/static/image.jpg">

<!-- Good -->
<img src="/static/image.jpg">
<!-- or -->
<img src="https://posaohub.me/static/image.jpg">
```

### Redirect Loop

If you're stuck in a redirect loop:

1. Check nginx logs: `docker-compose logs nginx`
2. Verify `X-Forwarded-Proto` header is set correctly
3. Make sure backend isn't doing its own redirects

## Testing SSL Configuration

### Online Tools

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html)

### Command Line Tests

```bash
# Test SSL connection
openssl s_client -connect posaohub.me:443 -servername posaohub.me

# Check certificate details
echo | openssl s_client -servername posaohub.me -connect posaohub.me:443 2>/dev/null | openssl x509 -noout -text

# Test HTTP to HTTPS redirect
curl -I http://posaohub.me

# Test HTTPS
curl -I https://posaohub.me
```

## Security Best Practices

1. **Use Strong Ciphers**: Already configured in the nginx config above
2. **Enable HSTS**: Already configured with `Strict-Transport-Security` header
3. **Regular Updates**: Keep certificates renewed (automatic with certbot)
4. **Monitor Expiry**: Set up alerts for certificate expiry
5. **Use HTTP/2**: Already enabled with `http2` directive
6. **Disable Old TLS**: Only TLS 1.2 and 1.3 enabled

## Certificate Monitoring

Create a script to check certificate expiry:

```bash
#!/bin/bash
# check-ssl-expiry.sh

DOMAIN="posaohub.me"
EXPIRY_DATE=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

echo "SSL certificate for $DOMAIN expires in $DAYS_LEFT days"

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: Certificate expires soon!"
    # Send notification (email, Slack, etc.)
fi
```

Run daily via cron:
```bash
0 9 * * * /home/deploy/check-ssl-expiry.sh
```

## Next Steps

After setting up HTTPS:

1. Update all absolute URLs in your application to use HTTPS
2. Test all functionality works over HTTPS
3. Update any external services with new HTTPS URLs
4. Configure HSTS preload (optional)
5. Monitor certificate expiry
6. Test automatic renewal

## Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)
