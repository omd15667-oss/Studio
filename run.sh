#!/bin/bash
# Digital Sovereignty Mirror - Quick Start

set -e

echo "🚀 DSM Quick Start"
echo "================="

if [ ! -d "venv" ]; then
    echo "📦 Creating venv..."
    python3 -m venv venv
fi

echo "✅ Activating venv..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

echo "📚 Installing dependencies..."
pip install -q -r backend/requirements.txt

echo "🗄️  Initializing database..."
python database/init_db.py

echo ""
echo "✨ ============================================"
echo "✨ DSM is ready to run!"
echo "✨ ============================================"
echo ""
echo "🚀 Starting API..."
echo ""

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload