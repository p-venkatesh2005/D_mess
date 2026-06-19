#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Creating necessary directories..."
mkdir -p static/uploads/payments

echo "✅ Build complete!"
echo "ℹ️  Database will be initialized on first application start"
