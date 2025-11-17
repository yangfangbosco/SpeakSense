#!/bin/bash

# SpeakSense - Start All Services
# This script starts all three services in the background

echo "Starting SpeakSense services..."
echo "================================"

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Kill existing processes on these ports (optional)
echo "Checking for existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start ASR Service
echo "Starting ASR Service on port 8001..."
cd "$PROJECT_ROOT/services/asr_service"
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
