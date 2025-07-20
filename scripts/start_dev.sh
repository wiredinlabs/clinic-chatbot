#!/bin/bash

echo "🚀 Starting Multi-Clinic Chatbot Development Server"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Copying from template..."
    cp .env.template .env
    echo "🔧 Please edit .env file with your configuration before running the server"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the development server
echo "🌟 Starting FastAPI development server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/api/v1/health"
echo ""
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info