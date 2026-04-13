import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User
from extensions import db

app = create_app()

with app.app_context():
    user = User.query.filter_by(phone='9090909090').first()
    if user:
        print(f"User found: {user.name}, Role: {user.role}")
        common_passwords = ['student123', 'worker123', 'admin123', 'password', '123456']
        found = False
        for p in common_passwords:
            if user.check_password(p):
                print(f"Password is: {p}")
                found = True
                break
        if not found:
            print("Password is custom (hashed). Cannot retrieve plaintext.")
            print("Hash:", user.password_hash)
    else:
        print("User with phone 9090909090 not found.")
