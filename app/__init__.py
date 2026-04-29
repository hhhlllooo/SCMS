# Application Package

import sys
import io
import os

# Handle Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import logging

load_dotenv()


def create_app(config_name=None):
    """Application factory function"""
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Ensure data directory exists (use absolute path based on app root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    uploads_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'backups'), exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Update config with absolute paths
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(data_dir, 'scms.db')}"
    app.config['UPLOAD_FOLDER'] = uploads_dir
    app.config['BACKUP_FOLDER'] = os.path.join(data_dir, 'backups')
    
    # Initialize extensions
    from app.models import db, User
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        if user_id == 'admin':
            return User(user_id)
        return None
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Register blueprints
    from app.routes import main, projects, settings, api
    app.register_blueprint(main)
    app.register_blueprint(projects)
    app.register_blueprint(settings)
    app.register_blueprint(api)
    
    # Context processor
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
