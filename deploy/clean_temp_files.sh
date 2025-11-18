#!/bin/bash

# SpeakSense Temporary Files Cleanup
# Removes all .pyc, __pycache__, .DS_Store and other temp files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "   Clean Temporary Files"
echo "============================================"
echo ""
echo "This will remove:"
echo "  - *.pyc (Python compiled files)"
echo "  - __pycache__/ (Python cache directories)"
echo "  - .DS_Store (macOS metadata)"
echo "  - *.swp, *.swo (Vim swap files)"
echo "  - *~ (Backup files)"
echo "  - .pytest_cache/"
echo "  - .mypy_cache/"
echo ""

cd "$PROJECT_ROOT"

# Show what will be deleted
echo -e "${BLUE}Files to be removed:${NC}"
find . -type f -name "*.pyc" | wc -l | xargs echo "  .pyc files:"
find . -type d -name "__pycache__" | wc -l | xargs echo "  __pycache__ directories:"
find . -type f -name ".DS_Store" | wc -l | xargs echo "  .DS_Store files:"
find . -type f -name "*.swp" -o -name "*.swo" -o -name "*~" | wc -l | xargs echo "  Swap/backup files:"

echo ""
read -p "Continue with cleanup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Cleaning...${NC}"

# Remove .pyc files
echo -n "Removing .pyc files... "
find . -type f -name "*.pyc" -delete
echo -e "${GREEN}✓${NC}"

# Remove __pycache__ directories
echo -n "Removing __pycache__ directories... "
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Remove .DS_Store files
echo -n "Removing .DS_Store files... "
find . -type f -name ".DS_Store" -delete
echo -e "${GREEN}✓${NC}"

# Remove vim swap files
echo -n "Removing swap files... "
find . -type f \( -name "*.swp" -o -name "*.swo" -o -name "*~" \) -delete
echo -e "${GREEN}✓${NC}"

# Remove pytest cache
echo -n "Removing .pytest_cache... "
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Remove mypy cache
echo -n "Removing .mypy_cache... "
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Remove Python egg-info
echo -n "Removing *.egg-info... "
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

echo ""
echo "============================================"
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo "============================================"
echo ""

# Show current directory size
echo "Current project size:"
du -sh "$PROJECT_ROOT" 2>/dev/null || echo "N/A"
echo ""
