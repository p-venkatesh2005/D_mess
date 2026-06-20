"""
Create admin user for Dwaraka Mess Management System
Run this script to create or reset the admin account
"""
import os
import sys

# Check for DATABASE_URL
if not os.environ.get('DATABASE_URL'):
    print("=" * 60)
    print("ERROR: DATABASE_URL environment variable not set!")
    print("=" * 60)
    print("Set it before running:")
    print('export DATABASE_URL="postgresql://user:pass@host/db"  # Linux/Mac')
    print('set DATABASE_URL=postgresql://user:pass@host/db        # Windows')
    print("=" * 60)
    sys.exit(1)

from app import create_app
from extensions import db
from models import User

def create_admin():
    """Create or update admin user"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get admin credentials from environment or use defaults
            admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            print("=" * 60)
            print("CREATING ADMIN USER")
            print("=" * 60)
            
            # Check if admin already exists
            admin = User.query.filter_by(phone=admin_phone).first()
            
            if admin:
                print(f"⚠️  Admin user already exists with phone: {admin_phone}")
                choice = input("Do you want to reset the password? (y/n): ").strip().lower()
                
                if choice == 'y':
                    admin.set_password(admin_password)
                    db.session.commit()
                    print(f"✅ Admin password reset successfully!")
                else:
                    print("❌ Operation cancelled")
                    return
            else:
                # Create new admin user
                admin = User(
                    name='Dwaraka Admin',
                    phone=admin_phone,
                    email='admin@dwaraka.com',
                    role='admin'
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                print(f"✅ Admin user created successfully!")
            
            print("=" * 60)
            print("ADMIN CREDENTIALS:")
            print("=" * 60)
            print(f"📱 Phone:    {admin_phone}")
            print(f"🔑 Password: {admin_password}")
            print("=" * 60)
            print("⚠️  IMPORTANT: Change this password after first login!")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ ERROR: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    create_admin()
