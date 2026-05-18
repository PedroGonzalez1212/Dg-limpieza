import os
from dotenv import load_dotenv

load_dotenv()  # Lee el archivo .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-dev-temporal'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///dev.db'  # SQLite para desarrollo local

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Railway lo inyecta

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}