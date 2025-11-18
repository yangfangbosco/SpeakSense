#!/bin/bash

# SpeakSense Backup Script
# Backs up database, audio files, and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="speaksense_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "============================================"
echo "   SpeakSense Backup Script"
echo "============================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_PATH"

echo "[1/4] Backing up databases..."
mkdir -p "$BACKUP_PATH/data"
cp -r "$PROJECT_ROOT/data/"*.db "$BACKUP_PATH/data/" 2>/dev/null || true
echo "✓ Databases backed up"

echo "[2/4] Backing up audio files..."
if [ -d "$PROJECT_ROOT/data/audio_files" ]; then
    cp -r "$PROJECT_ROOT/data/audio_files" "$BACKUP_PATH/data/" 2>/dev/null || true
fi
echo "✓ Audio files backed up"

echo "[3/4] Backing up configuration..."
mkdir -p "$BACKUP_PATH/config"
cp "$PROJECT_ROOT/config/config.yaml" "$BACKUP_PATH/config/" 2>/dev/null || true
echo "✓ Configuration backed up"

echo "[4/4] Creating archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"
echo "✓ Archive created"

# Keep only last 7 backups
echo ""
echo "Cleaning old backups (keeping last 7)..."
ls -t "$BACKUP_DIR"/speaksense_backup_*.tar.gz | tail -n +8 | xargs -r rm --

BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo "============================================"
echo "✅ Backup completed successfully!"
echo "============================================"
echo ""
echo "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "Backup size: $BACKUP_SIZE"
echo ""
echo "To restore from this backup:"
echo "  cd $PROJECT_ROOT"
echo "  ./deploy/restore.sh $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""
