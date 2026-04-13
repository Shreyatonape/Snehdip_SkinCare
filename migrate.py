#!/usr/bin/env python3
"""
Database migration and setup script for Flask application
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def create_app():
    """Create Flask application for migration"""
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:pass@123@localhost:5432/skincare_db"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    from extensions import db
    db.init_app(app)

    # Import models after db initialization
    from models import User, Doctor, Appointment, MedicalRecord, PatientRecord, DoctorAvailability, Message

    migrate = Migrate(app, db)

    return app

def reset_database():
    """Reset database completely - DANGEROUS: Use only in development"""
    app = create_app()

    with app.app_context():
        from extensions import db

        print("⚠️  WARNING: This will delete all data in the database!")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm == 'DELETE':
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables...")
            db.create_all()
            print("✅ Database reset successfully!")
        else:
            print("❌ Database reset cancelled!")

def init_database():
    """Initialize database with tables"""
    app = create_app()

    with app.app_context():
        from extensions import db

        print("Creating all tables...")
        db.create_all()
        print("✅ Database initialized successfully!")

def create_migration():
    """Create new migration"""
    app = create_app()

    with app.app_context():
        from flask_migrate import init, migrate, upgrade

        # Initialize migration repository if not exists
        if not os.path.exists('migrations'):
            print("Initializing migration repository...")
            init()
            print("✅ Migration repository initialized!")

        # Create migration
        print("Creating migration...")
        migrate(message="Initial migration")
        print("✅ Migration created!")

def apply_migrations():
    """Apply all pending migrations"""
    app = create_app()

    with app.app_context():
        from flask_migrate import upgrade

        print("Applying migrations...")
        upgrade()
        print("✅ Migrations applied successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate.py init     - Initialize database")
        print("  python migrate.py reset    - Reset database (DANGEROUS)")
        print("  python migrate.py create   - Create migration")
        print("  python migrate.py upgrade  - Apply migrations")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_database()
    elif command == "reset":
        reset_database()
    elif command == "create":
        create_migration()
    elif command == "upgrade":
        apply_migrations()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)