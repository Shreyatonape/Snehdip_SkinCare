#!/usr/bin/env python3
"""
Script to check existing doctors and create availability for all doctors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, DoctorAvailability, Doctor, User
from datetime import datetime, date, time, timedelta

def check_and_create_availability():
    """Check existing doctors and create availability for all"""

    with app.app_context():
        # Get all doctors
        doctors = User.query.filter_by(role='doctor').all()

        print(f"Found {len(doctors)} doctors in database:")

        for doctor_user in doctors:
            doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()
            print(f"  - User ID: {doctor_user.id}, Doctor ID: {doctor.id if doctor else 'None'}, Name: {doctor.name if doctor else doctor_user.username}")

        # Create availability for all doctors
        for doctor_user in doctors:
            doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()
            if not doctor:
                print(f"Skipping doctor {doctor_user.id} - no profile found")
                continue

            print(f"\nCreating availability for Dr. {doctor.name} (User ID: {doctor_user.id}, Doctor ID: {doctor.id})")

            # Clear existing availability for this doctor
            DoctorAvailability.query.filter_by(doctor_id=doctor.id).delete()
            db.session.commit()

            # Create availability slots for next 7 days
            for day_offset in range(7):
                slot_date = date.today() + timedelta(days=day_offset)

                # Create time slots from 9 AM to 5 PM with 1-hour intervals
                start_time = time(9, 0)  # 9:00 AM
                end_time = time(17, 0)   # 5:00 PM

                current_time = start_time
                slot_count = 0

                while current_time < end_time:
                    # Calculate slot end time
                    slot_end = time(
                        current_time.hour + 1,
                        current_time.minute
                    )

                    # Skip lunch break (12 PM - 1 PM)
                    if current_time.hour != 12:
                        availability = DoctorAvailability(
                            doctor_id=doctor.id,
                            date=slot_date,
                            start_time=current_time,
                            end_time=slot_end,
                            is_booked=False
                        )
                        db.session.add(availability)
                        slot_count += 1

                    # Move to next slot
                    current_time = slot_end

                print(f"  Created {slot_count} slots for {slot_date}")

            # Commit to database
            try:
                db.session.commit()
                print(f"✅ Availability created for Dr. {doctor.name}")

                # Verify creation
                total_slots = DoctorAvailability.query.filter_by(doctor_id=doctor.id).count()
                print(f"📊 Total slots for Dr. {doctor.name}: {total_slots}")

            except Exception as e:
                print(f"❌ Error creating availability for Dr. {doctor.name}: {e}")
                db.session.rollback()

if __name__ == "__main__":
    check_and_create_availability()