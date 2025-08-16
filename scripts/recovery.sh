#!/bin/bash
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
