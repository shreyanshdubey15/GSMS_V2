#!/usr/bin/env python
"""
Run script for Grocery Store Management System
"""
import os
import sys

# Change to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add current directory to Python path
sys.path.insert(0, script_dir)

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Grocery Store Management System...")
    print("📍 App URL: http://localhost:5000")
    print("👤 Admin login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)