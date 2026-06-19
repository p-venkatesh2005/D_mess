"""
WSGI entry point for production deployment
"""
import os
from app import create_app
from extensions import db
from models import User

# Create the Flask application instance
app = create_app(config_name='production')

# Initialize database and create admin on first run
with app.app_context():
    try:
        db.create_all()
        
        # Create admin if doesn't exist
        admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
        admin = User.query.filter_by(phone=admin_phone).first()
        
        if not admin:
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
            print(f"✅ Admin user created - Phone: {admin_phone}")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")

if __name__ == "__main__":
    app.run()
