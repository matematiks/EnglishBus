#!/bin/bash
# EnglishBus - Single Command Startup
# Usage: ./run.sh

set -e  # Exit on error

echo "🚌 EnglishBus Starting..."
echo ""

# Check Python version
python3 --version || { echo "❌ Python 3 required"; exit 1; }

# Check database exists
if [ ! -f "englishbus.db" ]; then
    echo "❌ Database not found: englishbus.db"
    echo "   Run data import first"
    exit 1
fi

# Optional: Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, pydantic, sqlite3" 2>/dev/null || {
    echo "⚠️  Installing dependencies..."
    pip3 install fastapi uvicorn pydantic
}

echo ""
echo "✅ All checks passed"
echo "🌍 Starting server..."
echo "   URL: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo "   Frontend: http://localhost:8001/"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
python3 -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload
