#!/bin/bash

# SpeakSense Server Sync Script
# Uses rsync to sync project to server, excluding unnecessary files

set -e

# Configuration
SERVER_USER="${SERVER_USER:-user}"
SERVER_HOST="${SERVER_HOST:-your-server}"
SERVER_PATH="${SERVER_PATH:-/opt/SpeakSense}"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================"
echo "   SpeakSense Server Sync"
echo "============================================"
echo ""

# Parse arguments or prompt
if [ -n "$1" ]; then
    SERVER_USER=$(echo "$1" | cut -d'@' -f1)
    SERVER_HOST=$(echo "$1" | cut -d'@' -f2 | cut -d':' -f1)
    SERVER_PATH=$(echo "$1" | cut -d':' -f2)
fi

if [ "$SERVER_HOST" = "your-server" ]; then
    echo -e "${YELLOW}Please provide server details:${NC}"
    read -p "Server user: " SERVER_USER
    read -p "Server host (IP or domain): " SERVER_HOST
    read -p "Server path (default: /opt/SpeakSense): " INPUT_PATH
    SERVER_PATH=${INPUT_PATH:-/opt/SpeakSense}
fi

echo "Sync target: $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Sync cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Starting rsync...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Rsync with exclusions
rsync -avz --progress \
  --exclude='*.pyc' \
  --exclude='__pycache__/' \
  --exclude='.DS_Store' \
  --exclude='.git/' \
  --exclude='.gitignore' \
  --exclude='*.log' \
  --exclude='logs/*.log' \
  --exclude='data/faq.db' \
  --exclude='data/*/faq.db' \
  --exclude='data/audio_files/*' \
  --exclude='data/*/audio_files/*' \
  --exclude='data/chromadb/*' \
  --exclude='data/*/chromadb/*' \
  --exclude='venv/' \
  --exclude='*.egg-info' \
  --exclude='*.swp' \
  --exclude='*.swo' \
  --exclude='*~' \
  --exclude='node_modules/' \
  --exclude='backups/*.tar.gz' \
  --exclude='*.tar.gz' \
  --exclude='.conda/' \
  --exclude='.cache/' \
  --exclude='.pytest_cache/' \
  --exclude='.mypy_cache/' \
  --exclude='dist/' \
  --exclude='build/' \
  --exclude='*.so' \
  --exclude='.idea/' \
  --exclude='.vscode/' \
  --exclude='*.db-journal' \
  --exclude='*.db-wal' \
  --exclude='*.db-shm' \
  ./ "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo -e "${GREEN}✅ Sync completed successfully!${NC}"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "  1. SSH to server:"
    echo "     ssh $SERVER_USER@$SERVER_HOST"
    echo ""
    echo "  2. Deploy on server:"
    echo "     cd $SERVER_PATH"
    echo "     ./deploy/deploy.sh"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Sync failed${NC}"
    echo "Please check the error messages above."
    exit 1
fi
