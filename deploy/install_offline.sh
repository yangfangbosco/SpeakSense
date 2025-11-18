#!/bin/bash

# Install from offline package (for servers without GitHub access)
# This script should be uploaded along with the offline package

set -e

if [ ! -d "offline-packages" ]; then
    echo "Error: offline-packages directory not found!"
    echo "Please extract offline-install-package.tar.gz first:"
    echo "  tar -xzf offline-install-package.tar.gz"
    exit 1
fi

echo "============================================"
echo "   Offline Installation"
echo "============================================"
echo ""

cd offline-packages

# Check if conda environment is activated
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Warning: No conda environment activated"
    echo "Please activate your environment first:"
    echo "  conda activate speaksense"
    exit 1
fi

echo "Installing in environment: $CONDA_DEFAULT_ENV"
echo ""

# Install MeloTTS
if [ -f "MeloTTS.zip" ]; then
    echo "[1/2] Installing MeloTTS..."
    if [ ! -d "MeloTTS-main" ]; then
        unzip -q MeloTTS.zip
    fi
    cd MeloTTS-main
    pip install . --no-deps
    cd ..
    echo "✓ MeloTTS installed"
else
    echo "⚠ MeloTTS.zip not found, skipping..."
fi

echo ""

# Install other packages
if [ -d "packages" ]; then
    echo "[2/2] Installing Python packages..."
    pip install --no-index --find-links=./packages ./packages/*
    echo "✓ Packages installed"
else
    echo "⚠ packages directory not found, skipping..."
fi

echo ""
echo "============================================"
echo "✅ Installation completed!"
echo "============================================"
echo ""
echo "Verify installation:"
echo "  python -c \"from melo.api import TTS; print('MeloTTS OK')\""
echo ""
