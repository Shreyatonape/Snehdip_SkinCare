#!/usr/bin/env python3
"""
Migration script to add missing columns to appointments table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_appointments_table():
    """Add missing patient_id, created_at, completed_at, reject_reason columns to appointments table"""

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host="localhost",
            database="skincare_db",
            user="postgres",
            password="pass@123"
        )
        cursor = conn.cursor()

        # Check current columns in appointments table
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'appointments'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]

        print("Current columns in appointments table:", existing_columns)

        # Add missing columns
        if 'patient_id' not in existing_columns:
            print("Adding patient_id column...")
            cursor.execute("""
                ALTER TABLE appointments
                ADD COLUMN patient_id INTEGER
            """)
        else:
            print("patient_id column already exists")

        if 'created_at' not in existing_columns:
            print("Adding created_at column...")
            cursor.execute("""
                ALTER TABLE appointments
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
        else:
            print("created_at column already exists")

        if 'completed_at' not in existing_columns:
            print("Adding completed_at column...")
            cursor.execute("""
                ALTER TABLE appointments
                ADD COLUMN completed_at TIMESTAMP
            """)
        else:
            print("completed_at column already exists")

        if 'reject_reason' not in existing_columns:
            print("Adding reject_reason column...")
            cursor.execute("""
                ALTER TABLE appointments
                ADD COLUMN reject_reason TEXT DEFAULT ''
            """)
        else:
            print("reject_reason column already exists")

        # Update patient_id from existing user emails
        print("Updating patient_id values from user emails...")
        cursor.execute("""
            UPDATE appointments
            SET patient_id = (
                SELECT id FROM users
                WHERE users.email = appointments.email
                LIMIT 1
            )
            WHERE patient_id IS NULL
        """)

        # Make patient_id NOT NULL after updating
        cursor.execute("""
            UPDATE appointments
            SET patient_id = 0
            WHERE patient_id IS NULL
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Appointments table migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    fix_appointments_table()