#!/bin/bash

# SpeakSense Restore Script
# Restores from a backup archive

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh "$PROJECT_ROOT/backups"/*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "============================================"
echo "   SpeakSense Restore Script"
echo "============================================"
echo ""
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "This will overwrite existing data. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "[1/4] Stopping services..."
cd "$PROJECT_ROOT"
./stop_all_services.sh 2>/dev/null || true
sleep 2
echo "✓ Services stopped"

echo "[2/4] Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
echo "✓ Backup extracted"

echo "[3/4] Restoring data..."
# Restore databases
if [ -d "$TEMP_DIR/$BACKUP_NAME/data" ]; then
    cp -r "$TEMP_DIR/$BACKUP_NAME/data/"*.db "$PROJECT_ROOT/data/" 2>/dev/null || true
fi

# Restore audio files
if [ -d "$TEMP_DIR/$BACKUP_NAME/data/audio_files" ]; then
    rm -rf "$PROJECT_ROOT/data/audio_files"
    cp -r "$TEMP_DIR/$BACKUP_NAME/data/audio_files" "$PROJECT_ROOT/data/"
fi

# Restore configuration
if [ -f "$TEMP_DIR/$BACKUP_NAME/config/config.yaml" ]; then
    cp "$TEMP_DIR/$BACKUP_NAME/config/config.yaml" "$PROJECT_ROOT/config/"
fi

echo "✓ Data restored"

echo "[4/4] Restarting services..."
./run_all_services.sh
sleep 5
echo "✓ Services restarted"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "============================================"
echo "✅ Restore completed successfully!"
echo "============================================"
echo ""
echo "Services are now running with restored data."
echo "Admin Portal: http://localhost:8090/portal/index.html"
echo ""
