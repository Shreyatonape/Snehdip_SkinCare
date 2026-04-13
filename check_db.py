import sqlite3
import os

def check_database():
    db_path = 'instance/skincare.db'

    if not os.path.exists(db_path):
        print("Database not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

        # Check if users table exists
        if ('users',) in tables:
            print("\nUsers table structure:")
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\n❌ No 'users' table found!")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database()