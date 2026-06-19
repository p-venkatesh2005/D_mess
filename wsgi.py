"""
WSGI entry point for production deployment
"""
import os
from app import create_app

# Create the Flask application instance
app = create_app(config_name='production')

if __name__ == "__main__":
    app.run()
