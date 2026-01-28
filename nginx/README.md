# Nginx Configuration

This directory contains nginx configurations for different environments.

## Files

- **nginx.conf** - Production configuration with HTTPS (default)
- **nginx.local.conf** - Local development configuration without HTTPS
- **Dockerfile** - Nginx container configuration

## Local Development (No SSL)

For local testing without SSL certificates:

### Option 1: Use Local Config (Recommended)

Update the Dockerfile to use local config:

```dockerfile
# Change this line:
COPY nginx.conf /etc/nginx/nginx.conf

# To this:
COPY nginx.local.conf /etc/nginx/nginx.conf
```

Then rebuild:
```bash
docker-compose up --build nginx
```

### Option 2: Comment Out SSL in nginx.conf

Comment out the HTTPS server block in `nginx.conf` (lines with `listen 443 ssl`).

## Production Deployment with SSL

The current `nginx.conf` is already configured for production with HTTPS.

### Prerequisites

- Domain DNS pointing to your server
- Ports 80 and 443 open on firewall

### Setup Steps on Server

1. **Obtain SSL Certificate**:

```bash
# Stop nginx
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone \
  -d posaohub.me \
  -d www.posaohub.me \
  --email your-email@example.com \
  --agree-tos
```

2. **Certificates will be at**:
```
/etc/letsencrypt/live/posaohub.me/fullchain.pem
/etc/letsencrypt/live/posaohub.me/privkey.pem
```

3. **Start nginx**:
```bash
docker-compose up -d nginx
```

4. **Verify HTTPS**:
```bash
curl -I https://posaohub.me
```

### Troubleshooting

**Certificate not found error:**
- Make sure certificates exist: `ls -la /etc/letsencrypt/live/posaohub.me/`
- Certificates are mounted in docker-compose.yml
- Check nginx logs: `docker-compose logs nginx`

**Nginx won't start:**
```bash
# Test configuration
docker-compose exec nginx nginx -t

# View detailed logs
docker-compose logs nginx
```

**HTTP works but HTTPS doesn't:**
- Check firewall: `sudo ufw status`
- Allow HTTPS: `sudo ufw allow 443/tcp`
- Verify port is listening: `sudo netstat -tlnp | grep :443`

## Configuration Details

### Production (nginx.conf)

- **HTTP (port 80)**: Redirects to HTTPS (except Let's Encrypt challenges)
- **HTTPS (port 443)**: Main application with SSL
- **Security headers**: HSTS, X-Frame-Options, etc.
- **Gzip compression**: Enabled for text files
- **Static file caching**: 30 days for /static/

### Local (nginx.local.conf)

- **HTTP only (port 80)**: No SSL
- Same proxy configuration as production
- Suitable for local development

## Switching Configurations

### For Local Development

Before starting locally, update `nginx/Dockerfile`:

```dockerfile
COPY nginx.local.conf /etc/nginx/nginx.conf
```

### For Production Deployment

Make sure `nginx/Dockerfile` has:

```dockerfile
COPY nginx.conf /etc/nginx/nginx.conf
```

## Testing Configuration

```bash
# Test nginx config syntax
docker-compose exec nginx nginx -t

# Reload nginx (without restart)
docker-compose exec nginx nginx -s reload

# View error logs
docker-compose logs nginx | grep error
```

## SSL Certificate Renewal

Certificates auto-renew via certbot systemd timer.

Manual renewal:
```bash
sudo certbot renew
docker-compose restart nginx
```

## Performance Tuning

Edit `nginx.conf` to adjust:

- `worker_connections`: Number of simultaneous connections
- `gzip_min_length`: Minimum file size for compression
- `client_max_body_size`: Maximum upload size
- Cache settings

## Security

Current security headers:
- ✅ HSTS (Strict-Transport-Security)
- ✅ X-Frame-Options
- ✅ X-Content-Type-Options
- ✅ X-XSS-Protection
- ✅ Referrer-Policy

TLS Configuration:
- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ Session caching enabled

## More Information

See [SSL_SETUP.md](../docs/SSL_SETUP.md) for complete SSL setup guide.
