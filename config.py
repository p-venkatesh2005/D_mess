import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # PostgreSQL Database Configuration with Connection Pooling
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'dwaraka_mess')
    
    # Use DATABASE_URL if provided (for cloud deployments like Heroku, Railway, Render)
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        # Fix for Render/Heroku - they use postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Build connection string with URL encoding for special characters
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}"
            f"@{db_host}:{db_port}/{db_name}"
        )
    
    # SQLAlchemy Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # Recycle connections every hour
        'pool_pre_ping': True,  # Test connections before using them
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'echo': False,  # Set to True for SQL query logging during development
    }
    
    # Application Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads/payments')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True
    # Enable SQL query logging in development
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 10,
        'echo': False,  # Set to True to see all SQL queries
    }

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_SSL_STRICT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),
        'pool_pre_ping': True,
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 40)),
        'echo': False,
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
