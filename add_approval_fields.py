#!/usr/bin/env python3
"""
Migration script to add is_approved and is_admin fields to users table
"""

import sqlite3
import os

def add_approval_fields():
    """Add is_approved and is_admin fields to user table"""

    db_path = 'instance/skincare.db'

    if not os.path.exists(db_path):
        print("Database not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_approved' not in columns:
            print("Adding is_approved column...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_approved BOOLEAN DEFAULT 0")
        else:
            print("is_approved column already exists")

        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        else:
            print("is_admin column already exists")

        # Set Snehal Kuldip Patil as admin if exists
        cursor.execute("""
            UPDATE user
            SET is_admin = 1, is_approved = 1
            WHERE username = 'Snehal Kuldip Patil'
        """)

        conn.commit()
        conn.close()

        print("✅ Database migration completed successfully!")
        print("✅ Snehal Kuldip Patil set as admin!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    add_approval_fields()