# Production Deployment Guide

## Overview
This guide covers deploying the Phishing Detector API to production with high availability, monitoring, and security.

## Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose
- Nginx
- SSL certificate
- Domain name
- Minimum 4GB RAM, 2 CPU cores

## Quick Start

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y
```

### 2. Application Deployment
```bash
# Clone repository
git clone <your-repo-url> /opt/phishing-detector
cd /opt/phishing-detector

# Setup environment
cp .env.production .env
# Edit .env with your configuration

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
python scripts/health_check.py
```

### 3. Nginx Configuration
```bash
# Copy nginx configuration
sudo cp config/nginx.conf /etc/nginx/sites-available/phishing-detector
sudo ln -s /etc/nginx/sites-available/phishing-detector /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 5. Monitoring Setup (Optional)
```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana: http://your-domain.com:3000
# Default credentials: admin/admin123
```

## Configuration

### Environment Variables
Edit `.env` file with your settings:
- `SECRET_KEY`: Change to a secure random key
- `ALLOWED_HOSTS`: Your domain name
- `CORS_ORIGINS`: Frontend domain
- Database and model paths

### Security Settings
- Enable firewall: `sudo ufw enable`
- Allow necessary ports: 80, 443, 22
- Regular security updates
- Monitor access logs

### Performance Tuning
- Adjust `MAX_WORKERS` based on CPU cores
- Configure rate limiting
- Set appropriate cache settings
- Monitor resource usage

## Maintenance

### Daily Tasks
- Check service status: `docker-compose ps`
- Monitor logs: `docker-compose logs --tail=100`
- Run health checks: `python scripts/health_check.py`

### Weekly Tasks
- Update system packages
- Review access logs
- Check disk usage
- Run backup script: `./scripts/backup.sh`

### Monthly Tasks
- Rotate logs
- Update Docker images
- Review security settings
- Performance analysis

## Backup and Recovery

### Automated Backups
```bash
# Setup daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/phishing-detector/scripts/backup.sh
```

### Manual Backup
```bash
./scripts/backup.sh
```

### Recovery
```bash
./scripts/recovery.sh backup_name
```

## Monitoring and Alerts

### Key Metrics to Monitor
- API response time
- Error rate
- CPU and memory usage
- Disk space
- Model prediction accuracy

### Setting Up Alerts
1. Configure Prometheus alerts in `monitoring/alert_rules.yml`
2. Setup AlertManager for notifications
3. Configure Grafana dashboards
4. Set up email/SMS notifications

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs phishing-detector-api

# Check configuration
python -m app.main --check-config

# Restart services
docker-compose restart
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Reduce workers if needed
# Edit MAX_WORKERS in .env

# Restart with new settings
docker-compose restart
```

#### Model Loading Issues
```bash
# Verify model file
ls -la models/

# Check model permissions
chmod 644 models/phishing_detector.joblib

# Test model loading
python -c "from app.ml_model import PhishingDetectionModel; m = PhishingDetectionModel(); m.load_model('models/phishing_detector.joblib')"
```

### Performance Optimization

#### Database Optimization
- Regular cleanup of old logs
- Index frequently queried fields
- Connection pooling

#### Caching
- Enable Redis for caching
- Cache model predictions
- Static file caching

#### Load Balancing
- Multiple API instances
- Nginx upstream configuration
- Health check endpoints

## Security Checklist

- [ ] SSL certificate installed and auto-renewing
- [ ] Firewall configured
- [ ] Strong passwords and keys
- [ ] Regular security updates
- [ ] Access logging enabled
- [ ] Rate limiting configured
- [ ] Security headers in Nginx
- [ ] Regular security audits

## Scaling

### Vertical Scaling
- Increase server resources
- Adjust worker count
- Optimize memory usage

### Horizontal Scaling
- Multiple server instances
- Load balancer configuration
- Shared storage for models
- Database clustering

## Support and Maintenance

### Log Files
- Application logs: `logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `journalctl -u phishing-detector`

### Monitoring URLs
- Health check: `/health`
- Metrics: `/metrics`
- API status: `/api/status`

### Contact Information
- System administrator: [email]
- Emergency contact: [phone]
- Documentation: [url]

---

For additional support, check the project documentation or contact the development team.
