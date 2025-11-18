#!/bin/bash

# SpeakSense Package Script
# Creates a deployment package excluding unnecessary files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PACKAGE_NAME="speaksense_$(date +%Y%m%d_%H%M%S).tar.gz"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_ROOT}"

echo "============================================"
echo "   SpeakSense Package Script"
echo "============================================"
echo ""

cd "$PROJECT_ROOT"

echo "Creating deployment package..."
echo "Package: $OUTPUT_DIR/$PACKAGE_NAME"
echo ""

# Create tar archive excluding unnecessary files
tar -czf "$OUTPUT_DIR/$PACKAGE_NAME" \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='*.log' \
  --exclude='logs/*.log' \
  --exclude='data/faq.db' \
  --exclude='data/*/faq.db' \
  --exclude='data/audio_files/*' \
  --exclude='data/*/audio_files/*' \
  --exclude='data/chromadb/*' \
  --exclude='data/*/chromadb/*' \
  --exclude='venv' \
  --exclude='*.egg-info' \
  --exclude='.DS_Store' \
  --exclude='*.swp' \
  --exclude='*.swo' \
  --exclude='node_modules' \
  --exclude='backups/*.tar.gz' \
  --exclude='*.tar.gz' \
  --exclude='.conda' \
  --exclude='.cache' \
  .

PACKAGE_SIZE=$(du -h "$OUTPUT_DIR/$PACKAGE_NAME" | cut -f1)

echo ""
echo "============================================"
echo "✅ Package created successfully!"
echo "============================================"
echo ""
echo "Package location: $OUTPUT_DIR/$PACKAGE_NAME"
echo "Package size: $PACKAGE_SIZE"
echo ""
echo "Next steps:"
echo "  1. Upload to server:"
echo "     scp $PACKAGE_NAME user@server:/path/to/"
echo ""
echo "  2. On server, extract and deploy:"
echo "     tar -xzf $PACKAGE_NAME"
echo "     cd SpeakSense"
echo "     ./deploy/deploy.sh"
echo ""
