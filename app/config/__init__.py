# Application Configuration

import os
from datetime import timedelta


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'project-management-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///data/scms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PER_PAGE = 20
    UPLOAD_FOLDER = 'uploads'
    BACKUP_FOLDER = 'data/backups'
    SENSITIVE_PASSWORD_HASH = os.getenv('SENSITIVE_PASSWORD_HASH')
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
