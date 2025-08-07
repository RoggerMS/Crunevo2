#!/usr/bin/env python3
import os
import psycopg2
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://postgres:ms0yt2Sn9M43UtN@crunevo-db.internal:5432/crunevo2"

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Query recent errors
    cur.execute("""
        SELECT id, ruta, mensaje, status_code, created_at 
        FROM system_error_log 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    errors = cur.fetchall()
    
    print("Recent System Errors:")
    print("=" * 80)
    
    if not errors:
        print("No errors found in system_error_log table.")
    else:
        for error in errors:
            error_id, ruta, mensaje, status_code, created_at = error
            print(f"ID: {error_id}")
            print(f"Route: {ruta}")
            print(f"Message: {mensaje}")
            print(f"Status Code: {status_code}")
            print(f"Created At: {created_at}")
            print("-" * 40)
    
    # Also check if user 'estudiante' exists
    cur.execute("SELECT id, username, email FROM users WHERE username = 'estudiante'")
    user = cur.fetchone()
    
    print("\nUser 'estudiante' check:")
    print("=" * 30)
    if user:
        print(f"User found - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
    else:
        print("User 'estudiante' not found in database.")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")