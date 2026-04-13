#!/usr/bin/env python3
"""
Migration script to add missing columns to doctors table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_doctors_table():
    """Add missing email, specialization, profile_image columns to doctors table"""

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host="localhost",
            database="skincare_db",
            user="postgres",
            password="pass@123"
        )
        cursor = conn.cursor()

        # Check current columns in doctors table
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'doctors'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]

        print("Current columns in doctors table:", existing_columns)

        # Add missing columns
        if 'email' not in existing_columns:
            print("Adding email column...")
            cursor.execute("""
                ALTER TABLE doctors
                ADD COLUMN email VARCHAR(100)
            """)
        else:
            print("email column already exists")

        if 'specialization' not in existing_columns:
            print("Adding specialization column...")
            cursor.execute("""
                ALTER TABLE doctors
                ADD COLUMN specialization VARCHAR(100)
            """)
        else:
            print("specialization column already exists")

        if 'profile_image' not in existing_columns:
            print("Adding profile_image column...")
            cursor.execute("""
                ALTER TABLE doctors
                ADD COLUMN profile_image VARCHAR(255) DEFAULT 'default_doctor.png'
            """)
        else:
            print("profile_image column already exists")

        # Update email from users table for existing doctors
        print("Updating doctor emails from users table...")
        cursor.execute("""
            UPDATE doctors
            SET email = (
                SELECT email FROM users
                WHERE users.id = doctors.user_id
                LIMIT 1
            )
            WHERE email IS NULL
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Doctors table migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    fix_doctors_table()