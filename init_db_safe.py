"""
Safe database initialization for production deployments.
Only creates tables if they don't exist - does NOT drop existing data.
Run: python init_db_safe.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def init_database_safe():
    """Create tables without dropping existing data"""
    try:
        from app import create_app
        from extensions import db
        from models import User
        
        # Check if DATABASE_URL is set
        if not os.environ.get('DATABASE_URL'):
            print("⚠️  DATABASE_URL not set, skipping database initialization")
            print("   (Database will be initialized on first app start)")
            return
        
        app = create_app()
        with app.app_context():
            print("🔨 Creating database tables (if not exists)...")
            db.create_all()
            
            # Check if admin exists
            admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
            admin = User.query.filter_by(phone=admin_phone).first()
            
            if not admin:
                print("👤 Creating admin user...")
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
                print(f"✅ Admin created - Phone: {admin_phone}")
            else:
                print(f"✅ Admin already exists - Phone: {admin_phone}")
            
            print("✅ Database initialization complete!")
            
    except Exception as e:
        print(f"⚠️  Database initialization skipped: {e}")
        print("   (Database will be initialized on first app start)")
        # Don't fail the build - let the app initialize DB on first run


if __name__ == '__main__':
    init_database_safe()
