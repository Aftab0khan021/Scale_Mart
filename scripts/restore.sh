#!/bin/bash
# Restore ScaleMart from backup
# Usage: ./restore.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_file>"
    echo "Example: ./restore.sh /backups/scalemart/scalemart_backup_20260130_020000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
TEMP_DIR="/tmp/scalemart_restore_$$"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will restore ScaleMart from backup"
echo "📁 Backup file: $BACKUP_FILE"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
echo "📦 Extracting backup..."
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Restore MongoDB
echo "📥 Restoring MongoDB..."
docker-compose up -d mongodb
sleep 10  # Wait for MongoDB to start

MONGODB_BACKUP=$(find "$TEMP_DIR" -type d -name "mongodb_*" | head -n 1)
if [ -d "$MONGODB_BACKUP" ]; then
    docker cp "$MONGODB_BACKUP" scalemart-mongodb:/data/restore
    docker-compose exec -T mongodb mongorestore --drop /data/restore
    echo "✅ MongoDB restored"
else
    echo "⚠️  MongoDB backup not found in archive"
fi

# Restore Redis
echo "📥 Restoring Redis..."
docker-compose up -d redis
sleep 5

REDIS_BACKUP=$(find "$TEMP_DIR" -name "redis_*.rdb" | head -n 1)
if [ -f "$REDIS_BACKUP" ]; then
    docker cp "$REDIS_BACKUP" scalemart-redis:/data/dump.rdb
    docker-compose restart redis
    echo "✅ Redis restored"
else
    echo "⚠️  Redis backup not found in archive"
fi

# Restore configuration
echo "📥 Restoring configuration..."
CONFIG_DIR=$(find "$TEMP_DIR" -type d -name "config_*" | head -n 1)
if [ -d "$CONFIG_DIR" ]; then
    cp "$CONFIG_DIR/backend.env" backend/.env 2>/dev/null || true
    cp "$CONFIG_DIR/frontend.env" frontend/.env 2>/dev/null || true
    echo "✅ Configuration restored"
else
    echo "⚠️  Configuration backup not found in archive"
fi

# Cleanup
rm -rf "$TEMP_DIR"

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Restore completed successfully"
echo "🔍 Verify the application at http://localhost:3000"
