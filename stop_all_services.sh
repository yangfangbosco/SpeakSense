#!/bin/bash

# SpeakSense - Stop All Services

echo "Stopping SpeakSense services..."

# Kill processes on service ports
echo "Stopping ASR Service (port 8001)..."
lsof -ti:8001 | xargs kill -9 2>/dev/null

echo "Stopping Retrieval Service (port 8002)..."
lsof -ti:8002 | xargs kill -9 2>/dev/null

echo "Stopping Admin Service (port 8003)..."
lsof -ti:8003 | xargs kill -9 2>/dev/null

echo ""
echo "All services stopped!"
