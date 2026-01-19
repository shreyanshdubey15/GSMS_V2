#!/usr/bin/env python
"""
Initialize the database for Grocery Store Management System
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

def init_db():
    app = create_app()

    with app.app_context():
        from extensions import db
        print("Creating database tables...")
        db.create_all()
        print("✅ Database initialized successfully!")

        # Create admin user
        from models import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / admin123")
        else:
            print("ℹ️  Admin user already exists")

if __name__ == '__main__':
    init_db()