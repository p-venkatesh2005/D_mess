#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p static/uploads/payments

# Initialize database tables (safe - doesn't drop data)
python init_db_safe.py
