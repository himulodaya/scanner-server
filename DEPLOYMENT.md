# Deployment Guide

This guide covers deploying Scanner Server in production environments.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 2GB RAM, 4GB recommended
- Network-accessible scanner and printer (optional)

## Production Deployment

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Create application directory
sudo mkdir -p /opt/scanner-server
cd /opt/scanner-server
```

### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/scanner-server.git .

# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Environment Configuration

Essential production settings in `.env`:

```bash
# Scanner settings
SCANNER_IP=192.168.1.100
SCANNER_PROTOCOL=escl
SCANNER_PORT=443

# Application settings
FLASK_DEBUG=0
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
LOG_LEVEL=warning

# Security
SECRET_KEY=<generate-strong-random-key>

# Optional: Discord notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Timezone
TZ=America/New_York
```

### 4. Build and Start

```bash
# Build the Docker image
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:5000/health

# Check logs
docker-compose logs scanner-server

# Access web interface
# Open http://your-server-ip:5000
```

## Reverse Proxy Setup

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name scanner.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scanner.example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/scanner.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scanner.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for scanning operations
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Increase client body size for file uploads
    client_max_body_size 50M;
}
```

### Traefik Configuration

```yaml
# docker-compose.yml with Traefik
services:
  scanner-server:
    build: .
    networks:
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.scanner.rule=Host(`scanner.example.com`)"
      - "traefik.http.routers.scanner.entrypoints=websecure"
      - "traefik.http.routers.scanner.tls.certresolver=letsencrypt"
      - "traefik.http.services.scanner.loadbalancer.server.port=5000"

networks:
  traefik:
    external: true
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Docker Security

```yaml
# docker-compose.yml security enhancements
services:
  scanner-server:
    security_opt:
      - no-new-privileges:true
    read_only: false  # Required for CUPS/SANE
    tmpfs:
      - /tmp
      - /run
    cap_drop:
      - ALL
    cap_add:
      - DAC_READ_SEARCH  # For scanner access
      - NET_RAW          # For network scanning
```

### 3. Environment Variables

Never commit `.env` file to version control:

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

Generate secure SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Backup and Recovery

### Backup Script

```bash
#!/bin/bash
# /opt/scanner-server/backup.sh

BACKUP_DIR="/backup/scanner-server"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/env_$DATE"
cp -r config "$BACKUP_DIR/config_$DATE"

# Backup scan data
docker run --rm \
  -v scanner_data:/data \
  -v "$BACKUP_DIR":/backup \
  ubuntu:24.04 \
  tar czf "/backup/scans_$DATE.tar.gz" /data

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and schedule:

```bash
chmod +x /opt/scanner-server/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/scanner-server/backup.sh >> /var/log/scanner-backup.log 2>&1
```

### Restore from Backup

```bash
# Stop container
docker-compose down

# Restore configuration
cp /backup/scanner-server/env_<timestamp> .env
cp -r /backup/scanner-server/config_<timestamp> config/

# Restore scan data
docker run --rm \
  -v scanner_data:/data \
  -v /backup/scanner-server:/backup \
  ubuntu:24.04 \
  tar xzf /backup/scans_<timestamp>.tar.gz -C /

# Start container
docker-compose up -d
```

## Monitoring

### Health Checks

```bash
# Create monitoring script
#!/bin/bash
# /opt/scanner-server/health-check.sh

HEALTH_URL="http://localhost:5000/health"
RESPONSE=$(curl -sf "$HEALTH_URL")

if [ $? -eq 0 ]; then
    echo "OK: Scanner Server is healthy"
    exit 0
else
    echo "CRITICAL: Scanner Server is down"
    # Send alert (email, Slack, etc.)
    exit 2
fi
```

### Log Monitoring

```bash
# View logs
docker-compose logs -f scanner-server

# Export logs
docker-compose logs scanner-server > scanner-server.log

# Log rotation (add to logrotate)
cat > /etc/logrotate.d/scanner-server << EOF
/var/log/scanner-server/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### Metrics with Prometheus

```yaml
# docker-compose.yml - add metrics exporter
services:
  scanner-server:
    # ... existing config ...

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

volumes:
  prometheus_data:
```

## Maintenance

### Updates

```bash
# Pull latest changes
cd /opt/scanner-server
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker image prune -a
```

### Database/Volume Cleanup

```bash
# Clean old scans (older than 90 days)
docker exec scanner-server find /data/scan -type f -mtime +90 -delete

# Clean temporary files
docker exec scanner-server find /data/scan/temp -type f -mtime +1 -delete
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs scanner-server

# Verify configuration
docker-compose config

# Test with debug mode
FLASK_DEBUG=1 docker-compose up
```

### Scanner Connection Issues

```bash
# Test from container
docker exec scanner-server ping <scanner-ip>
docker exec scanner-server hp-probe -bnet

# Check SANE
docker exec scanner-server scanimage -L
```

### Performance Issues

```bash
# Increase Gunicorn workers
# Edit .env
GUNICORN_WORKERS=4

# Adjust resource limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

## Production Checklist

- [ ] Environment variables configured
- [ ] FLASK_DEBUG=0 in production
- [ ] Reverse proxy with HTTPS configured
- [ ] Firewall rules applied
- [ ] Backup script scheduled
- [ ] Log rotation configured
- [ ] Health monitoring enabled
- [ ] Scanner connectivity tested
- [ ] Docker resources tuned
- [ ] Security headers configured
- [ ] Rate limiting verified
- [ ] Documentation reviewed

## Support

For production deployment assistance:
- GitHub Issues: https://github.com/yourusername/scanner-server/issues
- Documentation: https://github.com/yourusername/scanner-server/wiki
