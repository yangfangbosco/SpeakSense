#!/bin/bash

# SpeakSense Data Cleanup Script
# This script clears all FAQ data, audio files, and vector database for fresh deployment

set -e  # Exit on error

echo "============================================"
echo "SpeakSense Data Cleanup Script"
echo "============================================"
echo ""

# Step 1: Stop all services
echo "[1/6] Stopping all services..."
./stop_all_services.sh 2>/dev/null || true
sleep 2

# Step 2: Clear SQLite databases (truncate tables but keep schema)
echo "[2/6] Clearing FAQ databases..."

for db in "./data/faq.db" "./services/retrieval_service/data/faq.db" "./services/admin_service/data/faq.db"; do
    if [ -f "$db" ]; then
        echo "  - Clearing $db"
        # Only delete from tables that exist
        sqlite3 "$db" "DELETE FROM faq WHERE 1=1;" 2>/dev/null || true
        sqlite3 "$db" "DELETE FROM intents WHERE 1=1;" 2>/dev/null || true
        sqlite3 "$db" "DELETE FROM query_logs WHERE 1=1;" 2>/dev/null || true
        sqlite3 "$db" "VACUUM;"
    fi
done

# Step 3: Delete all audio files
echo "[3/6] Removing audio files..."
rm -rf ./data/audio_files/*
rm -rf ./services/admin_service/data/audio_files/*
echo "  - Audio files removed"

# Step 4: Clear ChromaDB vector database
echo "[4/6] Clearing vector database..."
rm -rf ./data/chromadb/*
rm -rf ./services/retrieval_service/data/chromadb/*
echo "  - Vector database cleared"

# Step 5: Clean up temporary preview audio files
echo "[5/6] Cleaning temporary files..."
rm -f /tmp/preview_*.wav 2>/dev/null || true
rm -f /tmp/test*.wav 2>/dev/null || true
rm -f /tmp/audio*.wav 2>/dev/null || true
echo "  - Temporary files cleaned"

# Step 6: Restart services
echo "[6/6] Restarting services..."
./run_all_services.sh
sleep 5

echo ""
echo "============================================"
echo "✅ Cleanup completed successfully!"
echo "============================================"
echo ""
echo "Summary:"
echo "  - All FAQ records deleted"
echo "  - All audio files removed"
echo "  - Vector database cleared"
echo "  - Temporary files cleaned"
echo "  - Services restarted"
echo ""
echo "Your SpeakSense instance is now ready for deployment!"
