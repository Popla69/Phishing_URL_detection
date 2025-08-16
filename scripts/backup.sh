#!/bin/bash
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
