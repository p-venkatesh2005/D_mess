"""
Production Database Setup Script for Dwaraka Mess Management System.
Run: python setup_production.py

This script initializes a clean, empty database and ONLY creates the 
necessities like the core Admin account based on environment variables.
"""
import os
import sys

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from extensions import db
from models import User


def setup_database():
    app = create_app()
    with app.app_context():
        print("🗑️  Warning: Dropping all existing data...")
        db.drop_all()
        
        print("🔨 Creating fresh tables...")
        db.create_all()

        # ─── ADMIN ───────────────────────────────────────────────────────────
        admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

        admin = User(
            name='Dwaraka Admin', 
            phone=admin_phone,
            email='admin@dwaraka.com', 
            role='admin'
        )
        admin.set_password(admin_password)
        db.session.add(admin)

        db.session.commit()
        
        print("✅ Fresh production database initialized successfully!")
        print("\n📋 SUPER ADMIN CREDENTIALS:")
        print(f"   🔑 Phone: {admin_phone}")
        print(f"   🔑 Password: [HIDDEN] (Set via ADMIN_PASSWORD in .env)")
        print("\nReady for deployment.")


if __name__ == '__main__':
    setup_database()
