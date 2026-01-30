#!/bin/bash
# Automated backup script for ScaleMart
# Run daily via cron: 0 2 * * * /path/to/backup.sh

set -e  # Exit on error

# Configuration
BACKUP_DIR="/backups/scalemart"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting ScaleMart backup - $DATE"

# Backup MongoDB
echo "📦 Backing up MongoDB..."
docker-compose exec -T mongodb mongodump --out=/data/backup/$DATE
docker cp scalemart-mongodb:/data/backup/$DATE "$BACKUP_DIR/mongodb_$DATE"
echo "✅ MongoDB backup complete"

# Backup Redis
echo "📦 Backing up Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5  # Wait for background save to complete
docker cp scalemart-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"
echo "✅ Redis backup complete"

# Backup environment files
echo "📦 Backing up configuration..."
mkdir -p "$BACKUP_DIR/config_$DATE"
cp backend/.env "$BACKUP_DIR/config_$DATE/backend.env" 2>/dev/null || true
cp frontend/.env "$BACKUP_DIR/config_$DATE/frontend.env" 2>/dev/null || true
echo "✅ Configuration backup complete"

# Compress backups
echo "🗜️  Compressing backups..."
cd "$BACKUP_DIR"
tar -czf "scalemart_backup_$DATE.tar.gz" \
    "mongodb_$DATE" \
    "redis_$DATE.rdb" \
    "config_$DATE"

# Remove uncompressed files
rm -rf "mongodb_$DATE" "redis_$DATE.rdb" "config_$DATE"
echo "✅ Compression complete"

# Remove old backups
echo "🧹 Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "scalemart_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo "✅ Cleanup complete"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/scalemart_backup_$DATE.tar.gz" | cut -f1)
echo "📊 Backup size: $BACKUP_SIZE"

# Optional: Upload to cloud storage (uncomment and configure)
# echo "☁️  Uploading to cloud storage..."
# aws s3 cp "$BACKUP_DIR/scalemart_backup_$DATE.tar.gz" s3://your-bucket/backups/
# echo "✅ Upload complete"

echo "✅ Backup completed successfully - $DATE"
echo "📁 Backup location: $BACKUP_DIR/scalemart_backup_$DATE.tar.gz"
