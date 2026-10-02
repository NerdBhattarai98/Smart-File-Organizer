#!/bin/bash

# Quick setup script for MongoDB integration

echo "=================================================="
echo "MongoDB Integration Setup"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "1. Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "   - Created backend/.env"
    echo "   - IMPORTANT: Edit this file with your MongoDB connection string"
    echo ""
fi

# Check MongoDB connection string
if grep -q "mongodb://localhost:27017" backend/.env; then
    echo "2. Checking for local MongoDB..."
    if ! command -v mongod &> /dev/null; then
        echo "   WARNING: mongod command not found"
        echo "   - Local MongoDB may not be installed"
        echo "   - Install with: brew install mongodb-community"
        echo "   - Or use MongoDB Atlas (cloud) instead"
    else
        echo "   - MongoDB found: $(mongod --version | head -1)"
    fi
    echo ""
fi

# Verify Python dependencies
echo "3. Verifying Python dependencies..."
cd backend
if python3 -c "import pymongo" 2>/dev/null; then
    echo "   - pymongo: OK"
else
    echo "   - pymongo: NOT INSTALLED"
    echo "   - Run: pip install pymongo==4.6.0"
fi

if python3 -c "import fastapi" 2>/dev/null; then
    echo "   - fastapi: OK"
else
    echo "   - fastapi: NOT INSTALLED"
fi

if python3 -c "import dotenv" 2>/dev/null; then
    echo "   - python-dotenv: OK"
else
    echo "   - python-dotenv: NOT INSTALLED"
fi

echo ""
echo "4. Configuration check..."
echo "   .env file location: $(pwd)/.env"
echo "   MongoDB URI: $(grep MONGO_URI backend/.env | cut -d'=' -f2)"
echo ""

echo "=================================================="
echo "Next steps:"
echo "=================================================="
echo ""
echo "Option A: Local MongoDB"
echo "  1. brew services start mongodb-community"
echo "  2. Keep MONGO_URI=mongodb://localhost:27017 in .env"
echo ""
echo "Option B: MongoDB Atlas (Cloud)"
echo "  1. Sign up at https://www.mongodb.com/cloud/atlas"
echo "  2. Create cluster and user"
echo "  3. Copy connection string"
echo "  4. Edit backend/.env and update MONGO_URI"
echo ""
echo "Then run the system:"
echo "  bash RUN_SYSTEM.sh"
echo ""
echo "Test MongoDB connection:"
echo "  curl http://localhost:8000/api/file-movement-stats"
echo ""
echo "View history in MongoDB Compass:"
echo "  Database: smart_file_organizer"
echo "  Collection: file_movements"
echo ""
