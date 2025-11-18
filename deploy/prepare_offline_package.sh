#!/bin/bash

# Prepare offline installation package for servers without GitHub access
# Run this script on a machine WITH internet access

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$PROJECT_ROOT/offline-packages"

echo "============================================"
echo "   Prepare Offline Installation Package"
echo "============================================"
echo ""

# Create package directory
mkdir -p "$PACKAGE_DIR"
cd "$PACKAGE_DIR"

echo "[1/3] Downloading MeloTTS from GitHub..."
curl -L https://github.com/myshell-ai/MeloTTS/archive/refs/heads/main.zip -o MeloTTS.zip
echo "✓ MeloTTS downloaded"

echo ""
echo "[2/3] Downloading Python packages..."
# Download all requirements
pip download -r "$PROJECT_ROOT/requirements.txt" -d ./packages 2>/dev/null || true
echo "✓ Packages downloaded"

echo ""
echo "[3/3] Creating archive..."
cd "$PROJECT_ROOT"
tar -czf offline-install-package.tar.gz offline-packages/
echo "✓ Archive created"

PACKAGE_SIZE=$(du -h offline-install-package.tar.gz | cut -f1)

echo ""
echo "============================================"
echo "✅ Offline package created!"
echo "============================================"
echo ""
echo "Package: $PROJECT_ROOT/offline-install-package.tar.gz"
echo "Size: $PACKAGE_SIZE"
echo ""
echo "Next steps:"
echo "  1. Upload to server:"
echo "     scp offline-install-package.tar.gz root@server:/tmp/"
echo ""
echo "  2. On server, run:"
echo "     cd /tmp"
echo "     tar -xzf offline-install-package.tar.gz"
echo "     cd offline-packages"
echo ""
echo "     # Install MeloTTS"
echo "     unzip MeloTTS.zip"
echo "     cd MeloTTS-main"
echo "     pip install ."
echo "     cd .."
echo ""
echo "     # Install other packages"
echo "     pip install --no-index --find-links=./packages -r /path/to/requirements.txt"
echo ""
