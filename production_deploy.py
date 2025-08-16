#!/usr/bin/env python3
"""
Production Deployment Script - Comprehensive deployment with monitoring and scaling
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

class ProductionDeployment:
    """Production deployment manager"""
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        self.deployment_config = {}
        self.status = {"services": {}, "checks": {}}
        
    def setup_environment(self):
        """Setup production environment"""
        print("🚀 Setting up production environment...")
        
        # Create production directories
        dirs = [
            "logs", "data", "models", "config", "backups",
            "monitoring", "ssl", "cache", "tmp"
        ]
        
        for dir_name in dirs:
            (self.project_root / dir_name).mkdir(exist_ok=True)
            print(f"✓ Created directory: {dir_name}")
        
        # Set permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(self.project_root / "logs", 0o755)
            os.chmod(self.project_root / "data", 0o755)
            os.chmod(self.project_root / "models", 0o755)
            print("✓ Set directory permissions")
        
        return True
    
    def create_production_config(self):
        """Create production configuration files"""
        print("📋 Creating production configuration...")
        
        # Production environment variables
        prod_env = """# Production Environment Variables
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
MAX_WORKERS=4
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Database (if used)
DATABASE_URL=sqlite:///./data/phishing_detector.db

# Model Configuration
MODEL_PATH=models/phishing_detector.joblib
MODEL_RETRAIN_INTERVAL=86400
FEATURE_CACHE_SIZE=1000

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
LOG_RETENTION_DAYS=30

# Performance
BATCH_SIZE_LIMIT=100
REQUEST_TIMEOUT=30
CACHE_TTL=3600
"""
        
        with open(self.project_root / ".env.production", "w") as f:
            f.write(prod_env)
        print("✓ Created .env.production")
        
        # Nginx configuration
        nginx_config = """# Nginx Configuration for Phishing Detector API
upstream phishing_detector {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001 backup;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_session_cache shared:SSL:1m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    limit_req zone=api burst=10 nodelay;
    
    # Logging
    access_log /var/log/nginx/phishing_detector.access.log;
    error_log /var/log/nginx/phishing_detector.error.log;
    
    # API proxy
    location /api/ {
        proxy_pass http://phishing_detector;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check
    location /health {
        proxy_pass http://phishing_detector/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
        
        with open(self.project_root / "config" / "nginx.conf", "w") as f:
            f.write(nginx_config)
        print("✓ Created nginx.conf")
        
        return True
    
    def create_docker_production_config(self):
        """Create production Docker configuration"""
        print("🐳 Creating production Docker configuration...")
        
        # Production Dockerfile
        dockerfile_prod = """FROM python:3.10-slim

# Security: Run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY models/ ./models/
COPY *.py ./

# Create necessary directories
RUN mkdir -p logs data cache tmp && \\
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""
        
        with open(self.project_root / "Dockerfile.prod", "w") as f:
            f.write(dockerfile_prod)
        print("✓ Created Dockerfile.prod")
        
        # Production docker-compose
        docker_compose_prod = """version: '3.8'

services:
  phishing-detector-api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./models:/app/models
      - ./cache:/app/cache
    restart: unless-stopped
    networks:
      - phishing-detector-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
  
  phishing-detector-api-backup:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8001:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./models:/app/models
      - ./cache:/app/cache
    restart: unless-stopped
    networks:
      - phishing-detector-network
    profiles:
      - backup
    depends_on:
      - phishing-detector-api
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - phishing-detector-api
    restart: unless-stopped
    networks:
      - phishing-detector-network
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
    restart: unless-stopped
    networks:
      - phishing-detector-network
    profiles:
      - monitoring
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped
    networks:
      - phishing-detector-network
    profiles:
      - monitoring
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    networks:
      - phishing-detector-network
    profiles:
      - cache

networks:
  phishing-detector-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
  redis-data:
"""
        
        with open(self.project_root / "docker-compose.prod.yml", "w") as f:
            f.write(docker_compose_prod)
        print("✓ Created docker-compose.prod.yml")
        
        return True
    
    def create_monitoring_config(self):
        """Create monitoring and observability configuration"""
        print("📊 Creating monitoring configuration...")
        
        # Prometheus configuration
        prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'phishing-detector-api'
    static_configs:
      - targets: ['phishing-detector-api:8000']
    metrics_path: /metrics
    scrape_interval: 5s
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: /nginx_status
    scrape_interval: 10s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
"""
        
        os.makedirs(self.project_root / "monitoring", exist_ok=True)
        with open(self.project_root / "monitoring" / "prometheus.yml", "w") as f:
            f.write(prometheus_config)
        
        # Alert rules
        alert_rules = """groups:
- name: phishing_detector_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"
      
  - alert: ServiceDown
    expr: up{job="phishing-detector-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "Phishing detector API is not responding"
"""
        
        with open(self.project_root / "monitoring" / "alert_rules.yml", "w") as f:
            f.write(alert_rules)
        
        print("✓ Created monitoring configuration")
        return True
    
    def create_backup_scripts(self):
        """Create backup and recovery scripts"""
        print("💾 Creating backup scripts...")
        
        # Backup script
        backup_script = """#!/bin/bash
# Backup script for Phishing Detector

BACKUP_DIR="/backups/phishing-detector"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="phishing_detector_backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup models
echo "Backing up models..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_models.tar.gz" models/

# Backup data
echo "Backing up data..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" data/

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" config/ .env.production

# Backup logs (last 7 days only)
echo "Backing up recent logs..."
find logs/ -name "*.log" -mtime -7 | tar -czf "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" -T -

# Create manifest
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" << EOF
Backup created: $(date)
Hostname: $(hostname)
Git commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Models: $(ls -la models/ | wc -l) files
Data: $(du -sh data/ | cut -f1)
Config files: $(ls config/ | wc -l) files
EOF

echo "Backup completed: $BACKUP_NAME"

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "phishing_detector_backup_*" -mtime +30 -delete
echo "Old backups cleaned"
"""
        
        with open(self.project_root / "scripts" / "backup.sh", "w") as f:
            f.write(backup_script)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(self.project_root / "scripts" / "backup.sh", 0o755)
        
        # Recovery script
        recovery_script = """#!/bin/bash
# Recovery script for Phishing Detector

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_name>"
    echo "Available backups:"
    ls /backups/phishing-detector/ | grep "_backup_"
    exit 1
fi

BACKUP_NAME=$1
BACKUP_DIR="/backups/phishing-detector"

if [ ! -f "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" ]; then
    echo "Error: Backup $BACKUP_NAME not found"
    exit 1
fi

echo "Restoring from backup: $BACKUP_NAME"
echo "Backup details:"
cat "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt"
echo

read -p "Continue with restore? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Stop services
echo "Stopping services..."
docker-compose -f docker-compose.prod.yml down

# Backup current state
echo "Backing up current state..."
CURRENT_BACKUP="current_state_$(date +%Y%m%d_%H%M%S)"
tar -czf "/tmp/${CURRENT_BACKUP}.tar.gz" models/ data/ config/

# Restore models
echo "Restoring models..."
tar -xzf "$BACKUP_DIR/${BACKUP_NAME}_models.tar.gz"

# Restore data
echo "Restoring data..."
tar -xzf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz"

# Restore configuration
echo "Restoring configuration..."
tar -xzf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"

# Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Recovery completed successfully"
echo "Current state backup saved to: /tmp/${CURRENT_BACKUP}.tar.gz"
"""
        
        os.makedirs(self.project_root / "scripts", exist_ok=True)
        with open(self.project_root / "scripts" / "recovery.sh", "w") as f:
            f.write(recovery_script)
        
        if os.name != 'nt':
            os.chmod(self.project_root / "scripts" / "recovery.sh", 0o755)
        
        print("✓ Created backup and recovery scripts")
        return True
    
    def create_systemd_services(self):
        """Create systemd service files for Linux deployment"""
        print("🔧 Creating systemd services...")
        
        systemd_service = """[Unit]
Description=Phishing Detector API
After=network.target
Wants=network.target

[Service]
Type=forking
User=appuser
Group=appuser
WorkingDirectory=/opt/phishing-detector
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/phishing-detector

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
"""
        
        os.makedirs(self.project_root / "config" / "systemd", exist_ok=True)
        with open(self.project_root / "config" / "systemd" / "phishing-detector.service", "w") as f:
            f.write(systemd_service)
        
        print("✓ Created systemd service file")
        return True
    
    def create_health_checks(self):
        """Create comprehensive health check system"""
        print("🏥 Creating health check system...")
        
        health_check_script = """#!/usr/bin/env python3
\"\"\"
Comprehensive health check system for Phishing Detector
\"\"\"

import requests
import json
import time
import sys
from datetime import datetime
import subprocess
import psutil
import os

class HealthChecker:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.checks = {}
        
    def check_api_health(self):
        \"\"\"Check API health endpoint\"\"\"
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.checks['api_health'] = {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
            else:
                self.checks['api_health'] = {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            self.checks['api_health'] = {'status': 'unhealthy', 'error': str(e)}
    
    def check_api_predict(self):
        \"\"\"Check prediction functionality\"\"\"
        test_url = "https://google.com"
        try:
            response = requests.post(
                f"{self.base_url}/predict",
                json={"url": test_url},
                timeout=15
            )
            if response.status_code == 200:
                self.checks['api_predict'] = {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
            else:
                self.checks['api_predict'] = {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            self.checks['api_predict'] = {'status': 'unhealthy', 'error': str(e)}
    
    def check_system_resources(self):
        \"\"\"Check system resource usage\"\"\"
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.checks['system_resources'] = {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available_gb': memory.available / (1024**3)
            }
            
            # Mark as unhealthy if resources are critically low
            if cpu_percent > 90 or memory.percent > 95 or disk.percent > 95:
                self.checks['system_resources']['status'] = 'unhealthy'
                
        except Exception as e:
            self.checks['system_resources'] = {'status': 'unhealthy', 'error': str(e)}
    
    def check_docker_services(self):
        \"\"\"Check Docker services status\"\"\"
        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.prod.yml', 'ps', '--services', '--filter', 'status=running'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                running_services = result.stdout.strip().split('\\n') if result.stdout.strip() else []
                self.checks['docker_services'] = {
                    'status': 'healthy' if running_services else 'unhealthy',
                    'running_services': running_services,
                    'service_count': len(running_services)
                }
            else:
                self.checks['docker_services'] = {'status': 'unhealthy', 'error': result.stderr}
                
        except Exception as e:
            self.checks['docker_services'] = {'status': 'unhealthy', 'error': str(e)}
    
    def check_model_files(self):
        \"\"\"Check if model files exist and are accessible\"\"\"
        model_path = "models/phishing_detector.joblib"
        try:
            if os.path.exists(model_path):
                stat = os.stat(model_path)
                self.checks['model_files'] = {
                    'status': 'healthy',
                    'model_size_mb': stat.st_size / (1024**2),
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                self.checks['model_files'] = {'status': 'unhealthy', 'error': 'Model file not found'}
        except Exception as e:
            self.checks['model_files'] = {'status': 'unhealthy', 'error': str(e)}
    
    def run_all_checks(self):
        \"\"\"Run all health checks\"\"\"
        print("🏥 Running health checks...")
        
        self.check_api_health()
        self.check_api_predict()
        self.check_system_resources()
        self.check_docker_services()
        self.check_model_files()
        
        # Overall health status
        unhealthy_checks = [name for name, check in self.checks.items() if check.get('status') != 'healthy']
        overall_status = 'healthy' if not unhealthy_checks else 'unhealthy'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'checks': self.checks,
            'unhealthy_checks': unhealthy_checks
        }

def main():
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] == 'healthy' else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
"""
        
        with open(self.project_root / "scripts" / "health_check.py", "w") as f:
            f.write(health_check_script)
        
        if os.name != 'nt':
            os.chmod(self.project_root / "scripts" / "health_check.py", 0o755)
        
        print("✓ Created health check system")
        return True
    
    def generate_deployment_guide(self):
        """Generate comprehensive deployment guide"""
        print("📚 Generating deployment guide...")
        
        deployment_guide = """# Production Deployment Guide

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
"""
        
        with open(self.project_root / "DEPLOYMENT.md", "w") as f:
            f.write(deployment_guide)
        
        print("✓ Created deployment guide")
        return True
    
    def run_deployment(self):
        """Run complete production deployment setup"""
        print("🚀 Starting production deployment setup...\n")
        
        steps = [
            ("Setting up environment", self.setup_environment),
            ("Creating production config", self.create_production_config),
            ("Creating Docker config", self.create_docker_production_config),
            ("Creating monitoring config", self.create_monitoring_config),
            ("Creating backup scripts", self.create_backup_scripts),
            ("Creating systemd services", self.create_systemd_services),
            ("Creating health checks", self.create_health_checks),
            ("Generating deployment guide", self.generate_deployment_guide),
        ]
        
        success_count = 0
        for step_name, step_function in steps:
            try:
                if step_function():
                    success_count += 1
                    print(f"✅ {step_name} completed\n")
                else:
                    print(f"❌ {step_name} failed\n")
            except Exception as e:
                print(f"❌ {step_name} failed: {e}\n")
        
        print(f"🎉 Production deployment setup completed!")
        print(f"✅ {success_count}/{len(steps)} steps successful")
        
        if success_count == len(steps):
            print("\n🚀 Next Steps:")
            print("1. Review configuration files in config/")
            print("2. Update .env.production with your settings")
            print("3. Build and deploy: docker-compose -f docker-compose.prod.yml up -d")
            print("4. Setup SSL certificate and domain")
            print("5. Configure monitoring and alerts")
            print("6. Test deployment with: python scripts/health_check.py")
            print("7. Setup automated backups")
            print("\n📚 See DEPLOYMENT.md for detailed instructions")
        
        return success_count == len(steps)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Deployment Setup')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    
    args = parser.parse_args()
    
    deployer = ProductionDeployment(args.project_root)
    success = deployer.run_deployment()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
