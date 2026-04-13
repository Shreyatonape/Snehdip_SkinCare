#!/usr/bin/env python3
"""
Check PostgreSQL database schema and current state
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_postgres_database():
    """Check PostgreSQL database structure"""

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host="localhost",
            database="skincare_db",
            user="postgres",
            password="pass@123"
        )
        cursor = conn.cursor()

        # List all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print("Tables in database:")
        for table in sorted(tables):
            print(f"  - {table}")

        # Check users table structure
        if 'users' in tables:
            print("\nUsers table structure:")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]}, nullable={col[2]}, default={col[3]})")
        else:
            print("\n❌ No 'users' table found!")

        # Check other important tables
        important_tables = ['doctors', 'appointments', 'medical_records']
        for table in important_tables:
            if table in tables:
                print(f"\n{table.title()} table structure:")
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}, nullable={col[2]})")
            else:
                print(f"\n❌ No '{table}' table found!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_postgres_database()