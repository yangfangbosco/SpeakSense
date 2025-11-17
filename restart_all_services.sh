#!/bin/bash

# SpeakSense - Restart All Services
# Stops all services and starts them again

echo "Restarting SpeakSense services..."
echo "================================"

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Stop all services
echo "Stopping all services..."
./stop_all_services.sh

# Wait for services to stop
sleep 2

# Start all services
echo "Starting all services..."
./run_all_services.sh

echo ""
echo "================================"
echo "Restart complete!"
echo "================================"
