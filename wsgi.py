"""
WSGI entry point for production deployment
"""
import os
import sys

# Debug: Check if DATABASE_URL is set
database_url = os.environ.get('DATABASE_URL')
print("=" * 60)
print("🔍 WSGI Startup Diagnostics")
print("=" * 60)
print(f"DATABASE_URL present: {bool(database_url)}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
print(f"ADMIN_PHONE: {os.environ.get('ADMIN_PHONE', 'not set')}")

if not database_url:
    print("=" * 60)
    print("❌ ERROR: DATABASE_URL environment variable is not set!")
    print("=" * 60)
    print("INSTRUCTIONS:")
    print("1. Go to Render Dashboard")
    print("2. Click on your Web Service")
    print("3. Go to 'Environment' tab")
    print("4. Add environment variable:")
    print("   Key: DATABASE_URL")
    print("   Value: Your PostgreSQL Internal Database URL")
    print("=" * 60)
    print("OR use Blueprint deployment with render.yaml")
    print("=" * 60)
    sys.exit(1)

from app import create_app
from extensions import db
from models import User

# Create the Flask application instance
app = create_app(config_name='production')

# Initialize database and create admin on first run
with app.app_context():
    try:
        print("🗄️  Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        
        # Create admin if doesn't exist
        admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
        admin = User.query.filter_by(phone=admin_phone).first()
        
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin = User(
                name='Dwaraka Admin',
                phone=admin_phone,
                email='admin@dwaraka.com',
                role='admin',
                is_active=True  # Explicitly set active
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user created - Phone: {admin_phone}")
        else:
            # Ensure existing admin is active
            if not admin.is_active:
                admin.is_active = True
                db.session.commit()
                print(f"✅ Admin user reactivated - Phone: {admin_phone}")
            else:
                print(f"✅ Admin user exists - Phone: {admin_phone}")
        
        print("=" * 60)
        print("🚀 Application ready to serve requests!")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ Database initialization error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    app.run()
