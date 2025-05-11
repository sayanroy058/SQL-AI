import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Database setup
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}
db.init_app(app)

# Initialize Flask-Migrate
migrate_instance = Migrate(app, db)

# Import models
from models import User, DatabaseConnection, Query

def run_migrations():
    """Run database migrations"""
    with app.app_context():
        # Initialize migrations directory if it doesn't exist
        try:
            init()
            print("Migrations directory initialized")
        except:
            print("Migrations directory already exists or initialization failed")
        
        # Create automatic migration
        try:
            migrate("Add db_type column to DatabaseConnection")
            print("Migration generated successfully")
        except Exception as e:
            print(f"Error generating migration: {str(e)}")
            
        # Apply migration
        try:
            upgrade()
            print("Database upgraded successfully")
        except Exception as e:
            print(f"Error upgrading database: {str(e)}")

if __name__ == '__main__':
    run_migrations()