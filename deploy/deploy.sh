#!/bin/bash

# SpeakSense Complete Deployment Script
# This script automates the entire deployment process

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================"
echo "   SpeakSense Deployment Script"
echo "============================================"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}[1/8] Checking prerequisites...${NC}"
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: conda not found. Please install Anaconda or Miniconda.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Conda found${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3 found${NC}"
echo ""

# Step 2: Create/Update Conda environment
echo -e "${BLUE}[2/8] Setting up Conda environment...${NC}"
if conda env list | grep -q "^speaksense "; then
    echo -e "${YELLOW}Conda environment 'speaksense' already exists.${NC}"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda deactivate 2>/dev/null || true
        conda remove -n speaksense --all -y
        conda create -n speaksense python=3.10 -y
    fi
else
    echo "Creating new environment..."
    conda create -n speaksense python=3.10 -y
fi
echo -e "${GREEN}✓ Conda environment ready${NC}"
echo ""

# Step 3: Activate environment and install dependencies
echo -e "${BLUE}[3/8] Installing Python dependencies...${NC}"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate speaksense

cd "$PROJECT_ROOT"
pip install -r requirements.txt

echo "Installing MeloTTS..."
pip install git+https://github.com/myshell-ai/MeloTTS.git

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Download models
echo -e "${BLUE}[4/8] Downloading AI models...${NC}"
echo "This may take several minutes on first run..."

echo "  - Downloading Whisper ASR model..."
python -c "import whisper; whisper.load_model('base')" 2>&1 | grep -v "FutureWarning" || true

echo "  - Downloading BGE embedding model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')" 2>&1 | grep -v "FutureWarning" || true

echo "  - Downloading MeloTTS models..."
python -c "from melo.api import TTS; tts_zh=TTS(language='ZH'); tts_en=TTS(language='EN')" 2>&1 | grep -v "FutureWarning" || true

echo -e "${GREEN}✓ Models downloaded${NC}"
echo ""

# Step 5: Configure server IP
echo -e "${BLUE}[5/8] Configuring server IP...${NC}"
if [ -z "$SERVER_IP" ]; then
    # Try to detect server IP
    DETECTED_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
    echo "Detected IP: $DETECTED_IP"
    read -p "Enter server IP (press Enter to use $DETECTED_IP): " INPUT_IP
    SERVER_IP=${INPUT_IP:-$DETECTED_IP}
fi
echo "Using IP: $SERVER_IP"
export SERVER_IP
echo -e "${GREEN}✓ Server IP configured${NC}"
echo ""

# Step 6: Initialize database
echo -e "${BLUE}[6/8] Initializing database...${NC}"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/logs"

# Database will be initialized automatically when services start
echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# Step 7: Start services
echo -e "${BLUE}[7/8] Starting services...${NC}"
cd "$PROJECT_ROOT"

# Stop any existing services
./stop_all_services.sh 2>/dev/null || true
sleep 2

# Start all services
SERVER_IP=$SERVER_IP ./run_all_services.sh

echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 8: Health check
echo -e "${BLUE}[8/8] Running health checks...${NC}"
sleep 5  # Wait for services to fully start

check_service() {
    local name=$1
    local port=$2
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo -e "${GREEN}✓ $name (port $port) - OK${NC}"
        return 0
    else
        echo -e "${RED}✗ $name (port $port) - FAILED${NC}"
        return 1
    fi
}

HEALTH_OK=true
check_service "ASR Service" 8001 || HEALTH_OK=false
check_service "Retrieval Service" 8002 || HEALTH_OK=false
check_service "Admin Service" 8003 || HEALTH_OK=false

echo ""

if [ "$HEALTH_OK" = true ]; then
    echo "============================================"
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo "============================================"
    echo ""
    echo "Service URLs:"
    echo "  Admin Portal:  http://$SERVER_IP:8090/portal/index.html"
    echo "  Testing Portal: http://$SERVER_IP:8080/web/index.html"
    echo ""
    echo "API Documentation:"
    echo "  ASR:       http://$SERVER_IP:8001/docs"
    echo "  Retrieval: http://$SERVER_IP:8002/docs"
    echo "  Admin:     http://$SERVER_IP:8003/docs"
    echo ""
    echo "Logs:"
    echo "  tail -f $PROJECT_ROOT/logs/*.log"
    echo ""
    echo "To stop services:"
    echo "  $PROJECT_ROOT/stop_all_services.sh"
    echo ""
else
    echo "============================================"
    echo -e "${RED}⚠️  Deployment completed with errors${NC}"
    echo "============================================"
    echo ""
    echo "Please check the logs for details:"
    echo "  tail -f $PROJECT_ROOT/logs/*.log"
    echo ""
    exit 1
fi
