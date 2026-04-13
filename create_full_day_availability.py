#!/usr/bin/env python3
"""
Create full day time slots for doctor availability
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def create_full_day_availability():
    """Create full day availability slots for doctors"""

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host="localhost",
            database="skincare_db",
            user="postgres",
            password="pass@123"
        )
        cursor = conn.cursor()

        # Clear existing availability to avoid conflicts
        print("Clearing existing availability...")
        cursor.execute("DELETE FROM doctor_availability")

        # Get all doctors
        cursor.execute("SELECT id, name FROM doctors")
        doctors = cursor.fetchall()

        if not doctors:
            print("❌ No doctors found!")
            return

        # Create full day availability for next 14 days
        for doctor_id, doctor_name in doctors:
            print(f"Creating availability for Dr. {doctor_name}...")

            for day_offset in range(14):
                date = datetime.now().date() + timedelta(days=day_offset)

                # Skip weekends (optional - remove if you want weekends too)
                if date.weekday() >= 5:  # Saturday=5, Sunday=6
                    continue

                # Create full day slots (every 30 minutes)
                current_time = datetime.strptime('09:00', '%H:%M').time()
                end_time = datetime.strptime('18:00', '%H:%M').time()

                slot_count = 0
                while current_time < end_time:
                    next_time = (datetime.combine(date, current_time) + timedelta(minutes=30)).time()

                    # Create slot
                    cursor.execute("""
                        INSERT INTO doctor_availability
                        (doctor_id, date, start_time, end_time, is_booked)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (doctor_id, date, current_time, next_time, False))

                    current_time = next_time
                    slot_count += 1

                print(f"  - {date.strftime('%Y-%m-%d')}: {slot_count} slots created")

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Full day availability created successfully!")
        print("📅 Available slots: 9:00 AM - 6:00 PM (every 30 minutes)")
        print("📅 Duration: Next 14 days (weekdays only)")

    except Exception as e:
        print(f"❌ Error during availability creation: {e}")

if __name__ == "__main__":
    create_full_day_availability()