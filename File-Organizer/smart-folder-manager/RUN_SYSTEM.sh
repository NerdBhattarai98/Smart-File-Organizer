#!/bin/bash

# Smart Folder Manager - Complete Startup Script
# This script starts both backend and frontend servers

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project Directory: $PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Smart Folder Manager Setup${NC}"
echo -e "${YELLOW}================================${NC}\n"

# Resolve Python executable
PYTHON_CMD=""
PIP_CMD=""

# Kill any existing processes
echo -e "${YELLOW} Stopping any existing servers...${NC}"
pkill -f "backend/main.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
if lsof -ti :8000 >/dev/null 2>&1; then
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
fi
if lsof -ti :5173 >/dev/null 2>&1; then
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
fi
sleep 1

# Start Backend
echo -e "${YELLOW} Starting Backend Server...${NC}"
cd "$PROJECT_DIR/backend"
if [ -x "$PROJECT_DIR/backend/venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_DIR/backend/venv/bin/python"
    PIP_CMD="$PROJECT_DIR/backend/venv/bin/pip"
elif [ -x "$PROJECT_DIR/../.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_DIR/../.venv/bin/python"
    PIP_CMD="$PROJECT_DIR/../.venv/bin/pip"
elif command -v python3 >/dev/null 2>&1; then
    python3 -m venv venv
    PYTHON_CMD="$PROJECT_DIR/backend/venv/bin/python"
    PIP_CMD="$PROJECT_DIR/backend/venv/bin/pip"
else
    echo -e "${RED} Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="$(command -v python3 || command -v python)"
fi

if [ -z "$PIP_CMD" ]; then
    PIP_CMD="$PYTHON_CMD -m pip"
fi

if [ -x "$PIP_CMD" ]; then
    "$PIP_CMD" install -q -r requirements.txt 2>/dev/null || echo "Dependencies already installed"
else
    $PIP_CMD install -q -r requirements.txt 2>/dev/null || echo "Dependencies already installed"
fi
"$PYTHON_CMD" main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN} Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
sleep 3
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}Backend failed to start. Check /tmp/backend.log${NC}"
    cat /tmp/backend.log
    exit 1
fi
echo -e "${GREEN} Backend is healthy${NC}\n"

# Start Frontend
echo -e "${YELLOW} Starting Frontend Server...${NC}"
cd "$PROJECT_DIR/frontend"
npm install --legacy-peer-deps > /tmp/frontend-install.log 2>&1 || true
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN} Frontend started (PID: $FRONTEND_PID)${NC}"

sleep 2
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN} System Ready!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Handle cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '\n${YELLOW}Servers stopped${NC}'; exit 0" SIGINT

# Keep script running
wait
