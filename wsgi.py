#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn
"""
import os
from app import app, create_tables

if __name__ == "__main__":
    # Create tables if they don't exist
    create_tables()
    
    # Run with Gunicorn in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
