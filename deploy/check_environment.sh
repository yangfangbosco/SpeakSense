#!/bin/bash

# SpeakSense Environment Check Script
# Verifies that the system meets all requirements

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "   SpeakSense Environment Check"
echo "============================================"
echo ""

ALL_OK=true

check_command() {
    local cmd=$1
    local name=$2
    local required=$3

    echo -n "Checking $name... "
    if command -v "$cmd" &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | head -n1)
        echo -e "${GREEN}✓${NC} Found: $VERSION"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗ NOT FOUND (Required)${NC}"
            ALL_OK=false
        else
            echo -e "${YELLOW}⚠ NOT FOUND (Optional)${NC}"
        fi
        return 1
    fi
}

check_python_package() {
    local package=$1
    local name=$2

    echo -n "Checking Python package $name... "
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Installed"
        return 0
    else
        echo -e "${RED}✗ NOT INSTALLED${NC}"
        ALL_OK=false
        return 1
    fi
}

echo "=== System Requirements ==="
check_command "python3" "Python 3" "true"
check_command "conda" "Conda" "true"
check_command "git" "Git" "true"
check_command "curl" "curl" "true"

echo ""
echo "=== System Information ==="
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Distribution: $NAME $VERSION"
fi
echo "Total RAM: $(free -h 2>/dev/null | grep Mem | awk '{print $2}' || echo 'N/A')"
echo "Free Disk: $(df -h . | tail -1 | awk '{print $4}')"

echo ""
echo "=== Checking Conda Environment ==="
if conda env list | grep -q "speaksense"; then
    echo -e "${GREEN}✓${NC} Conda environment 'speaksense' exists"

    # Activate and check packages
    source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
    if conda activate speaksense 2>/dev/null; then
        echo ""
        echo "=== Checking Python Packages ==="
        check_python_package "fastapi" "FastAPI"
        check_python_package "whisper" "OpenAI Whisper"
        check_python_package "chromadb" "ChromaDB"
        check_python_package "torch" "PyTorch"
        check_python_package "sentence_transformers" "Sentence Transformers"

        echo ""
        echo "Python version: $(python --version)"
        echo "pip version: $(pip --version)"
    fi
else
    echo -e "${RED}✗${NC} Conda environment 'speaksense' not found"
    echo "  Run: ./deploy/deploy.sh to create it"
    ALL_OK=false
fi

echo ""
echo "=== Checking Required Ports ==="
check_port() {
    local port=$1
    local name=$2

    echo -n "Port $port ($name)... "
    if lsof -i:$port &> /dev/null; then
        echo -e "${YELLOW}IN USE${NC}"
    else
        echo -e "${GREEN}AVAILABLE${NC}"
    fi
}

check_port 8001 "ASR Service"
check_port 8002 "Retrieval Service"
check_port 8003 "Admin Service"
check_port 8080 "Testing Portal"
check_port 8090 "Admin Portal"

echo ""
echo "=== Checking Project Structure ==="
check_dir() {
    local dir=$1
    local name=$2

    echo -n "$name... "
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} exists"
    else
        echo -e "${RED}✗${NC} missing"
        ALL_OK=false
    fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
check_dir "services/asr_service" "ASR Service"
check_dir "services/retrieval_service" "Retrieval Service"
check_dir "services/admin_service" "Admin Service"
check_dir "portal" "Admin Portal"
check_dir "config" "Configuration"

echo ""
echo "============================================"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✅ Environment check passed!${NC}"
    echo "System is ready for deployment."
    echo ""
    echo "Next steps:"
    echo "  1. Run deployment: ./deploy/deploy.sh"
    echo "  2. Or start services: ./run_all_services.sh"
else
    echo -e "${RED}⚠️  Environment check failed${NC}"
    echo "Please fix the issues above before deploying."
    echo ""
    echo "For help, see: DEPLOYMENT.md"
fi
echo "============================================"

[ "$ALL_OK" = true ] && exit 0 || exit 1
