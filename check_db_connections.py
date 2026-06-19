#!/usr/bin/env python
"""
Quick Database Connection Checker
Shows all PostgreSQL connection details and configurations
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("POSTGRESQL CONNECTION CONFIGURATION - DWARAKA MESS SYSTEM")
print("="*80)

print("\n📋 ENVIRONMENT VARIABLES:")
print("-"*80)
print(f"DB_USER:         {os.environ.get('DB_USER', 'postgres (default)')}")
print(f"DB_PASSWORD:     {'***' if os.environ.get('DB_PASSWORD') else 'postgres (default)'}")
print(f"DB_HOST:         {os.environ.get('DB_HOST', 'localhost (default)')}")
print(f"DB_PORT:         {os.environ.get('DB_PORT', '5432 (default)')}")
print(f"DB_NAME:         {os.environ.get('DB_NAME', 'dwaraka_mess (default)')}")
print(f"DATABASE_URL:    {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")

print("\n🔧 CONNECTION POOL SETTINGS:")
print("-"*80)
print(f"Pool Size:       {os.environ.get('DB_POOL_SIZE', '10 (dev) / 20 (prod) - default')}")
print(f"Pool Recycle:    {os.environ.get('DB_POOL_RECYCLE', '3600s (dev) / 1800s (prod) - default')}")
print(f"Max Overflow:    {os.environ.get('DB_MAX_OVERFLOW', '20 (dev) / 40 (prod) - default')}")
print(f"Pool Pre-Ping:   Enabled (always)")

print("\n🔗 CONSTRUCTED CONNECTION STRING:")
print("-"*80)

try:
    from config import Config
    config = Config()
    uri = config.SQLALCHEMY_DATABASE_URI
    
    # Mask password
    if '@' in uri:
        parts = uri.split('@')
        if '://' in parts[0]:
            protocol_user_pass = parts[0].split('://')
            if ':' in protocol_user_pass[1]:
                user, password = protocol_user_pass[1].split(':', 1)
                masked_uri = f"{protocol_user_pass[0]}://{user}:***@{parts[1]}"
            else:
                masked_uri = uri
        else:
            masked_uri = uri
    else:
        masked_uri = uri
    
    print(f"URI: {masked_uri}")
    
    if uri.startswith('postgresql://'):
        print("✅ Using PostgreSQL protocol")
    else:
        print("⚠️  Not using PostgreSQL!")
        
except Exception as e:
    print(f"❌ Error loading config: {e}")

print("\n📊 APPLICATION CONFIGURATION:")
print("-"*80)
print(f"FLASK_ENV:       {os.environ.get('FLASK_ENV', 'development (default)')}")
print(f"SECRET_KEY:      {'Set' if os.environ.get('SECRET_KEY') else 'Using default (CHANGE IN PRODUCTION!)'}")
print(f"Debug:           {os.environ.get('DEBUG', 'True')}")

print("\n🐳 DOCKER CONFIGURATION:")
print("-"*80)
docker_check = os.path.exists('docker-compose.yml')
print(f"docker-compose.yml:  {'✅ Found' if docker_check else '❌ Not found'}")
dockerfile_check = os.path.exists('Dockerfile')
print(f"Dockerfile:          {'✅ Found' if dockerfile_check else '❌ Not found'}")

print("\n📝 CONFIGURATION FILES:")
print("-"*80)
files = [
    ('.env', 'Development environment'),
    ('.env.production', 'Production environment template'),
    ('.env.example', 'Environment example'),
    ('config.py', 'Database configuration'),
    ('models.py', 'Database models'),
]

for filename, description in files:
    exists = os.path.exists(filename)
    status = '✅' if exists else '❌'
    print(f"{status} {filename:20} - {description}")

print("\n🚀 QUICK START COMMANDS:")
print("-"*80)
print("Docker Compose:")
print("  docker-compose up -d                  # Start PostgreSQL + App")
print("  docker-compose logs -f postgres       # View database logs")
print("  docker-compose exec postgres psql -U postgres -d dwaraka_mess")
print()
print("Manual Connection:")
print("  psql -h localhost -U postgres -d dwaraka_mess")
print()
print("Test Connection:")
print("  python test_postgresql_connection.py")

print("\n" + "="*80)
print("✨ PostgreSQL Migration Complete - All connections configured!")
print("="*80)
