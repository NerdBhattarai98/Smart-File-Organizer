#!/bin/bash
# Setup Script for Smart Folder Manager
# Run this script to set up both frontend and backend

echo "================================================"
echo "Smart Folder Manager - Complete Setup"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check Node version
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"
echo ""

# Backend Setup
echo "================================================"
echo "BACKEND SETUP"
echo "================================================"
cd backend

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate

echo "2. Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "3. Creating log directory..."
mkdir -p app/logs
touch app/logs/app.log

echo "✅ Backend setup complete!"
echo ""

# Frontend Setup
echo "================================================"
echo "FRONTEND SETUP"
echo "================================================"
cd ../frontend

echo "1. Installing Node dependencies..."
npm install

echo "2. Building Vite config..."
# Vite is configured in package.json

echo "✅ Frontend setup complete!"
echo ""

# Final instructions
echo "================================================"
echo "SETUP COMPLETE!"
echo "================================================"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Happy Organizing! 🚀"
