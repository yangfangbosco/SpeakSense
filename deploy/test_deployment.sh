#!/bin/bash

# SpeakSense Deployment Test Script
# Tests all services to ensure deployment is successful

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "   SpeakSense Deployment Test"
echo "============================================"
echo ""

# Detect server IP
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name=$1
    local test_command=$2

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo -e "${BLUE}[1/4] Testing Service Health${NC}"
run_test "ASR Service Health" "curl -s http://$SERVER_IP:8001/health"
run_test "Retrieval Service Health" "curl -s http://$SERVER_IP:8002/health"
run_test "Admin Service Health" "curl -s http://$SERVER_IP:8003/health"
echo ""

echo -e "${BLUE}[2/4] Testing ASR Service${NC}"
# Create a test audio file (silent audio)
TEST_AUDIO="/tmp/test_audio.wav"
python3 -c "
import wave
import struct
with wave.open('$TEST_AUDIO', 'w') as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(16000)
    f.writeframes(struct.pack('<h', 0) * 16000)
"

run_test "ASR Transcription API" "curl -s -F 'file=@$TEST_AUDIO' http://$SERVER_IP:8001/transcribe"
rm -f "$TEST_AUDIO"
echo ""

echo -e "${BLUE}[3/4] Testing Admin Service${NC}"
run_test "FAQ Creation API" "curl -s -X POST http://$SERVER_IP:8003/admin/faqs \
    -H 'Content-Type: application/json' \
    -d '{\"question\":\"测试问题\",\"answer\":\"测试答案\",\"language\":\"zh\",\"category\":\"test\"}'"

run_test "FAQ List API" "curl -s http://$SERVER_IP:8003/admin/faqs"
echo ""

echo -e "${BLUE}[4/4] Testing Retrieval Service${NC}"
run_test "Query API" "curl -s -X POST http://$SERVER_IP:8002/query \
    -H 'Content-Type: application/json' \
    -d '{\"question\":\"测试问题\"}'"
echo ""

# Clean up test data
echo "Cleaning up test data..."
FAQ_ID=$(curl -s http://$SERVER_IP:8003/admin/faqs | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['answer_id'] if data else '')" 2>/dev/null || echo "")
if [ -n "$FAQ_ID" ]; then
    curl -s -X DELETE "http://$SERVER_IP:8003/admin/faqs/$FAQ_ID" > /dev/null
fi

echo ""
echo "============================================"
echo "   Test Results"
echo "============================================"
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo "Deployment is successful and all services are working correctly."
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
    echo "Please check the service logs for details:"
    echo "  tail -f $PROJECT_ROOT/logs/*.log"
    exit 1
fi
