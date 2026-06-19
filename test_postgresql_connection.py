#!/usr/bin/env python
"""
PostgreSQL Connection Test Script
Tests all database connections and configurations for Dwaraka Mess System
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.RESET} {text}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ{Colors.RESET} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")

def test_imports():
    """Test if all required packages are installed"""
    print_header("Testing Package Imports")
    
    packages = {
        'flask': 'Flask',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'psycopg2': 'psycopg2-binary',
        'sqlalchemy': 'SQLAlchemy',
        'dotenv': 'python-dotenv'
    }
    
    all_passed = True
    for package, name in packages.items():
        try:
            __import__(package)
            print_success(f"{name} imported successfully")
        except ImportError as e:
            print_error(f"{name} failed to import: {e}")
            all_passed = False
    
    return all_passed

def test_config_loading():
    """Test configuration loading"""
    print_header("Testing Configuration Loading")
    
    try:
        from config import config, Config
        print_success("Config module imported successfully")
        
        # Test default config
        default_config = config['default']
        print_success(f"Default config: {default_config.__name__}")
        
        # Test development config
        dev_config = config['development']
        print_success(f"Development config: {dev_config.__name__}")
        
        # Test production config
        prod_config = config['production']
        print_success(f"Production config: {prod_config.__name__}")
        
        return True
    except Exception as e:
        print_error(f"Config loading failed: {e}")
        return False

def test_database_uri():
    """Test database URI construction"""
    print_header("Testing Database URI Construction")
    
    try:
        from config import Config
        
        print_info("Environment Variables:")
        print(f"  DB_USER: {os.environ.get('DB_USER', 'Not set (using default: postgres)')}")
        print(f"  DB_PASSWORD: {'***' if os.environ.get('DB_PASSWORD') else 'Not set (using default)'}")
        print(f"  DB_HOST: {os.environ.get('DB_HOST', 'Not set (using default: localhost)')}")
        print(f"  DB_PORT: {os.environ.get('DB_PORT', 'Not set (using default: 5432)')}")
        print(f"  DB_NAME: {os.environ.get('DB_NAME', 'Not set (using default: dwaraka_mess)')}")
        print()
        
        # Construct URI
        config_obj = Config()
        uri = config_obj.SQLALCHEMY_DATABASE_URI
        
        # Mask password in output
        masked_uri = uri
        if '@' in uri:
            parts = uri.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                if len(user_pass) > 2:
                    masked_uri = f"{user_pass[0]}:{user_pass[1]}:***@{parts[1]}"
        
        print_success(f"Database URI constructed: {masked_uri}")
        
        # Check if it's PostgreSQL
        if uri.startswith('postgresql://'):
            print_success("✓ Using PostgreSQL protocol")
        else:
            print_warning("⚠ Not using PostgreSQL protocol")
        
        return True
    except Exception as e:
        print_error(f"Database URI construction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test Flask app creation"""
    print_header("Testing Flask App Creation")
    
    try:
        from app import create_app
        app = create_app('development')
        print_success("Flask app created successfully")
        
        print_info(f"App name: {app.name}")
        print_info(f"Debug mode: {app.debug}")
        print_info(f"Database URI: postgresql://...")
        
        return True, app
    except Exception as e:
        print_error(f"App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_database_connection(app):
    """Test actual database connection"""
    print_header("Testing Database Connection")
    
    if not app:
        print_error("App not available, skipping connection test")
        return False
    
    try:
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            # Test simple query
            result = db.session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print_success(f"Database connection successful (test query returned: {row[0]})")
            
            # Get PostgreSQL version
            result = db.session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print_success(f"PostgreSQL version: {version.split(',')[0]}")
            
            return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_warning("Make sure PostgreSQL is running and credentials are correct")
        import traceback
        traceback.print_exc()
        return False

def test_connection_pool(app):
    """Test connection pool configuration"""
    print_header("Testing Connection Pool Configuration")
    
    if not app:
        print_error("App not available, skipping pool test")
        return False
    
    try:
        from extensions import db
        
        with app.app_context():
            engine = db.engine
            pool = engine.pool
            
            print_info(f"Pool class: {pool.__class__.__name__}")
            print_info(f"Pool size: {pool.size()}")
            print_info(f"Pool timeout: {pool._timeout}")
            print_info(f"Max overflow: {pool._max_overflow}")
            print_info(f"Pool recycle: {engine.pool_recycle}")
            print_info(f"Pool pre-ping: {engine.pool_pre_ping}")
            
            # Check current connections
            print_info(f"Current checked out connections: {pool.checkedout()}")
            
            print_success("Connection pool configured correctly")
            return True
    except Exception as e:
        print_error(f"Connection pool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models_loading(app):
    """Test if models can be loaded"""
    print_header("Testing Model Loading")
    
    if not app:
        print_error("App not available, skipping model test")
        return False
    
    try:
        from models import (User, Student, Payment, Subscription, Order, Menu,
                           Attendance, LeaveRequest, Announcement, Feedback,
                           QRScan, Hostler, RoomListing)
        
        models = [
            User, Student, Payment, Subscription, Order, Menu,
            Attendance, LeaveRequest, Announcement, Feedback,
            QRScan, Hostler, RoomListing
        ]
        
        with app.app_context():
            for model in models:
                print_success(f"Model loaded: {model.__name__}")
        
        print_info(f"Total models: {len(models)}")
        return True
    except Exception as e:
        print_error(f"Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_table_creation(app):
    """Test if tables can be created"""
    print_header("Testing Table Creation")
    
    if not app:
        print_error("App not available, skipping table creation test")
        return False
    
    try:
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print_success("db.create_all() executed successfully")
            
            # List all tables
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                print_success(f"Found {len(tables)} tables in database:")
                for table in tables:
                    print(f"  • {table}")
            else:
                print_warning("No tables found in database")
            
            return True
    except Exception as e:
        print_error(f"Table creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crud_operations(app):
    """Test basic CRUD operations"""
    print_header("Testing CRUD Operations")
    
    if not app:
        print_error("App not available, skipping CRUD test")
        return False
    
    try:
        from extensions import db
        from models import User
        from datetime import datetime
        
        with app.app_context():
            # CREATE
            test_user = User(
                name='Test User',
                phone='0000000000',
                email='test@example.com',
                role='student'
            )
            test_user.set_password('test123')
            
            db.session.add(test_user)
            db.session.commit()
            print_success("CREATE: Test user created")
            
            # READ
            found_user = User.query.filter_by(phone='0000000000').first()
            if found_user:
                print_success(f"READ: Test user found (ID: {found_user.id})")
            else:
                print_error("READ: Test user not found")
                return False
            
            # UPDATE
            found_user.name = 'Updated Test User'
            db.session.commit()
            
            updated_user = User.query.filter_by(phone='0000000000').first()
            if updated_user.name == 'Updated Test User':
                print_success("UPDATE: Test user updated successfully")
            else:
                print_error("UPDATE: Test user update failed")
            
            # DELETE
            db.session.delete(updated_user)
            db.session.commit()
            
            deleted_user = User.query.filter_by(phone='0000000000').first()
            if deleted_user is None:
                print_success("DELETE: Test user deleted successfully")
            else:
                print_error("DELETE: Test user deletion failed")
                return False
            
            print_success("All CRUD operations completed successfully")
            return True
    except Exception as e:
        print_error(f"CRUD operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relationships(app):
    """Test model relationships"""
    print_header("Testing Model Relationships")
    
    if not app:
        print_error("App not available, skipping relationship test")
        return False
    
    try:
        from extensions import db
        from models import User, Student
        from sqlalchemy import inspect
        
        with app.app_context():
            # Check User relationships
            user_relationships = inspect(User).relationships
            print_info(f"User model relationships: {[r.key for r in user_relationships]}")
            print_success(f"User has {len(user_relationships)} relationships")
            
            # Check Student relationships
            student_relationships = inspect(Student).relationships
            print_info(f"Student model relationships: {[r.key for r in student_relationships]}")
            print_success(f"Student has {len(student_relationships)} relationships")
            
            return True
    except Exception as e:
        print_error(f"Relationship test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.GREEN}PostgreSQL Connection Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}Dwaraka Mess Management System{Colors.RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Run all tests
    results['imports'] = test_imports()
    results['config'] = test_config_loading()
    results['uri'] = test_database_uri()
    
    app_created, app = test_app_creation()
    results['app_creation'] = app_created
    
    if app:
        results['connection'] = test_database_connection(app)
        results['pool'] = test_connection_pool(app)
        results['models'] = test_models_loading(app)
        results['tables'] = test_table_creation(app)
        results['crud'] = test_crud_operations(app)
        results['relationships'] = test_relationships(app)
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed! PostgreSQL connection is working perfectly.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Please check the errors above.{Colors.RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
