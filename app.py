"""
Dwaraka Mess Management System
Main Application Entry Point
"""
import os
from flask import Flask, redirect, url_for, render_template
from config import config
from extensions import db, login_manager, csrf
from models import User


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Ensure upload folder exists
    upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.student import student_bp
    from blueprints.worker import worker_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(worker_bp, url_prefix='/worker')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Root redirect
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'worker':
                return redirect(url_for('worker.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return render_template('index.html')

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=os.environ.get('DEBUG', 'True') == 'True', host='0.0.0.0', port=5000)
