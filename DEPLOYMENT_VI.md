# 📝 Triển Khai Sản Xuất - Production Deployment Guide

## Prerequisites (Yêu Cầu Tiên Quyết)

- Ubuntu/Debian server hoặc tương đương
- Docker và Docker Compose installed
- Domain name (optional but recommended)
- SSL Certificate (Let's Encrypt)
- Sufficient disk space (30GB+ for models and videos)
- GPU (optional nhưng recommended cho Whisper)

## 1. Server Setup (Thiết Lập Server)

### SSH vào server
```bash
ssh user@your-server-ip
```

### Update system packages
```bash
sudo apt update && sudo apt upgrade -y
```

### Install dependencies
```bash
sudo apt install -y git curl wget
```

### Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 2. Application Deployment

### Clone repository
```bash
cd /home/app
sudo git clone <your-repo-url> video-translator
cd video-translator
```

### Create production .env
```bash
sudo nano .env
```

**Production .env values:**
```env
# Database
DATABASE_URL=postgresql://produser:strong_password@postgres:5432/video_translator_prod
DATABASE_USER=produser
DATABASE_PASSWORD=strong_password
DATABASE_NAME=video_translator_prod

# Redis
REDIS_URL=redis://redis:6379/0

# Backend
BACKEND_URL=https://your-domain.com
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=False

# Frontend
FRONTEND_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://your-domain.com/api

# File Upload
MAX_UPLOAD_SIZE=10737418240  # 10GB
UPLOAD_DIR=/data/uploads
PROCESSED_DIR=/data/processed

# Whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cuda  # if GPU available

# Google Translate
GOOGLE_TRANSLATE_API_KEY=your-production-key
```

### Create data directories
```bash
sudo mkdir -p /data/uploads /data/processed
sudo chown 1000:1000 /data/uploads /data/processed
```

### Update Docker Compose for production
```bash
sudo nano docker/docker-compose.yml
```

**Key changes:**
- Remove `--reload` from backend command
- Add health checks
- Configure resource limits
- Use environment variables

### Start production services
```bash
cd docker
sudo docker-compose up -d
sudo docker-compose logs -f
```

## 3. Nginx Reverse Proxy Setup

### Install Nginx
```bash
sudo apt install -y nginx
```

### Create Nginx config
```bash
sudo nano /etc/nginx/sites-available/video-translator
```

**Configuration:**
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    # API backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Large file upload support
        client_max_body_size 10G;
        proxy_request_buffering off;
        proxy_buffering off;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable site
```bash
sudo ln -s /etc/nginx/sites-available/video-translator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 4. SSL Certificate Setup (Let's Encrypt)

### Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Generate certificate
```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

### Auto-renewal
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## 5. Monitoring & Logging

### View Docker logs
```bash
# Backend
docker logs video-translator-backend -f

# Worker
docker logs video-translator-worker -f

# Frontend
docker logs video-translator-frontend -f

# Database
docker logs video-translator-db -f
```

### Monitor system resources
```bash
docker stats
```

### Database backup
```bash
# Backup
docker exec video-translator-db pg_dump -U produser video_translator_prod > backup.sql

# Restore
docker exec -i video-translator-db psql -U produser video_translator_prod < backup.sql
```

## 6. Database Maintenance

### Create backup script
```bash
#!/bin/bash
BACKUP_DIR="/backups/video-translator"
mkdir -p $BACKUP_DIR
docker exec video-translator-db pg_dump -U produser video_translator_prod | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz
# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Schedule backups (crontab)
```bash
sudo crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /path/to/backup-script.sh
```

## 7. Performance Tuning

### PostgreSQL optimization
```bash
docker exec video-translator-db psql -U produser -d video_translator_prod -c "
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
"
```

### Redis optimization
```bash
docker exec video-translator-redis redis-cli CONFIG SET maxmemory 512mb
```

### Celery worker tuning
Update `docker-compose.yml`:
```yaml
command: celery -A app.workers.tasks worker --loglevel=info --concurrency=4
```

## 8. Monitoring & Alerting

### Install Prometheus (optional)
```bash
sudo docker pull prom/prometheus
# Configure Prometheus to scrape your services
```

### Health check script
```bash
#!/bin/bash
curl -f http://localhost:8000/api/v1/health || exit 1
echo "API is healthy"
```

## 9. Troubleshooting

### Check Docker status
```bash
docker-compose ps
docker-compose logs -f
```

### Rebuild images
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Reset database
```bash
docker-compose down -v
docker-compose up -d
```

## 10. Auto-Scaling & Load Balancing

### Scale workers
```bash
# Increase Celery workers in docker-compose.yml
worker:
  deploy:
    replicas: 4
```

### Load balancer config
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

**Production deployment completed! 🚀**
