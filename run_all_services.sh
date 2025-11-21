#!/bin/bash

# SpeakSense - Start All Services
# This script starts all three services in the background

echo "Starting SpeakSense services..."
echo "================================"

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate conda environment
source ~/opt/anaconda3/etc/profile.d/conda.sh
conda activate speaksense

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# ========================================
# Auto-detect Server IP for Portal Configuration
# ========================================

# Allow manual override: SERVER_IP=192.168.1.100 ./run_all_services.sh
if [ -z "$SERVER_IP" ]; then
    # Try to auto-detect the server's IP address
    # Method 1: Try to get primary network interface IP
    SERVER_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+')

    # Method 2: If method 1 fails, try hostname -I
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # Method 3: If both fail, use localhost
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="localhost"
    fi
fi

echo "Detected Server IP: $SERVER_IP"
echo "Note: Override with: SERVER_IP=your.ip.address ./run_all_services.sh"
echo ""

# Configure portal URLs
if [ "$SERVER_IP" != "localhost" ]; then
    echo "Configuring portals for IP: $SERVER_IP"

    # Backup original files if they don't exist
    if [ ! -f "$PROJECT_ROOT/portal/assets/js/app.js.original" ]; then
        cp "$PROJECT_ROOT/portal/assets/js/app.js" "$PROJECT_ROOT/portal/assets/js/app.js.original"
    fi
    if [ ! -f "$PROJECT_ROOT/web/index.html.original" ]; then
        cp "$PROJECT_ROOT/web/index.html" "$PROJECT_ROOT/web/index.html.original"
    fi

    # Replace localhost with server IP in portal files
    sed "s|'http://localhost:8001'|'http://$SERVER_IP:8001'|g" \
        "$PROJECT_ROOT/portal/assets/js/app.js.original" > "$PROJECT_ROOT/portal/assets/js/app.js"
    sed "s|'http://localhost:8002'|'http://$SERVER_IP:8002'|g" \
        "$PROJECT_ROOT/portal/assets/js/app.js" > "$PROJECT_ROOT/portal/assets/js/app.js.tmp" && \
        mv "$PROJECT_ROOT/portal/assets/js/app.js.tmp" "$PROJECT_ROOT/portal/assets/js/app.js"
    sed "s|'http://localhost:8003'|'http://$SERVER_IP:8003'|g" \
        "$PROJECT_ROOT/portal/assets/js/app.js" > "$PROJECT_ROOT/portal/assets/js/app.js.tmp" && \
        mv "$PROJECT_ROOT/portal/assets/js/app.js.tmp" "$PROJECT_ROOT/portal/assets/js/app.js"

    # Same for testing portal
    sed "s|'http://localhost:8001'|'http://$SERVER_IP:8001'|g" \
        "$PROJECT_ROOT/web/index.html.original" > "$PROJECT_ROOT/web/index.html"
    sed "s|'http://localhost:8002'|'http://$SERVER_IP:8002'|g" \
        "$PROJECT_ROOT/web/index.html" > "$PROJECT_ROOT/web/index.html.tmp" && \
        mv "$PROJECT_ROOT/web/index.html.tmp" "$PROJECT_ROOT/web/index.html"
    sed "s|'http://localhost:8003'|'http://$SERVER_IP:8003'|g" \
        "$PROJECT_ROOT/web/index.html" > "$PROJECT_ROOT/web/index.html.tmp" && \
        mv "$PROJECT_ROOT/web/index.html.tmp" "$PROJECT_ROOT/web/index.html"

    echo "✓ Portal configuration updated for IP: $SERVER_IP"
else
    echo "Using localhost configuration (development mode)"
fi
echo ""

# Kill existing processes on these ports (optional)
echo "Checking for existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start ASR Service
echo "Starting ASR Service on port 8001..."
cd "$PROJECT_ROOT/services/asr_service"
export KMP_DUPLICATE_LIB_OK=TRUE
nohup python main.py > "$PROJECT_ROOT/logs/asr_service.log" 2>&1 &
ASR_PID=$!
echo "ASR Service started (PID: $ASR_PID)"

# Wait a bit for service to start
sleep 2

# Start Retrieval Service
echo "Starting Retrieval Service on port 8002..."
cd "$PROJECT_ROOT/services/retrieval_service"
nohup python main.py > "$PROJECT_ROOT/logs/retrieval_service.log" 2>&1 &
RETRIEVAL_PID=$!
echo "Retrieval Service started (PID: $RETRIEVAL_PID)"

# Wait a bit
sleep 2

# Start Admin Service
echo "Starting Admin Service on port 8003..."
cd "$PROJECT_ROOT/services/admin_service"
nohup python main.py > "$PROJECT_ROOT/logs/admin_service.log" 2>&1 &
ADMIN_PID=$!
echo "Admin Service started (PID: $ADMIN_PID)"

# Wait a bit
sleep 2

# Start Web Testing Portal
echo "Starting Web Testing Portal on port 8080..."
cd "$PROJECT_ROOT/web"
nohup python server.py > "$PROJECT_ROOT/logs/web_server.log" 2>&1 &
WEB_PID=$!
echo "Web Testing Portal started (PID: $WEB_PID)"

# Wait a bit
sleep 1

# Start Admin Portal
echo "Starting Admin Portal on port 8090..."
cd "$PROJECT_ROOT/portal"
nohup python server.py > "$PROJECT_ROOT/logs/portal_server.log" 2>&1 &
PORTAL_PID=$!
echo "Admin Portal started (PID: $PORTAL_PID)"

echo ""
echo "================================"
echo "All services started!"
echo "================================"
echo ""
echo "Service URLs:"
echo "  ASR Service:       http://localhost:8001"
echo "  Retrieval Service: http://localhost:8002"
echo "  Admin Service:     http://localhost:8003"
echo ""
echo "🌐 Admin Portal (Production):"
echo "  http://localhost:8090/portal/index.html"
echo ""
echo "🔧 Testing Portal (Development):"
echo "  http://localhost:8080/web/index.html"
echo ""
echo "API Documentation:"
echo "  http://localhost:8001/docs"
echo "  http://localhost:8002/docs"
echo "  http://localhost:8003/docs"
echo ""
echo "Logs:"
echo "  tail -f logs/asr_service.log"
echo "  tail -f logs/retrieval_service.log"
echo "  tail -f logs/admin_service.log"
echo "  tail -f logs/web_server.log"
echo ""
echo "To stop all services:"
echo "  ./stop_all_services.sh"
echo ""
