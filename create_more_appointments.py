import sys
sys.path.append('.')
from app import app
from extensions import db
from models import User, Appointment, Doctor
from datetime import datetime
app.app_context().push()

print('=== CREATE MORE TEST APPOINTMENTS ===')

# Get patients and doctors
patients = User.query.filter_by(role='patient').all()
doctor_users = User.query.filter_by(role='doctor').all()

print(f'Available patients: {len(patients)}')
print(f'Available doctors: {len(doctor_users)}')

# Create appointments for all valid combinations
created_count = 0

for patient in patients:
    for doctor_user in doctor_users:
        # Check if doctor exists in doctors table
        doctor_record = Doctor.query.filter_by(user_id=doctor_user.id).first()

        if doctor_record:
            # Check if appointment already exists
            existing_appointment = Appointment.query.filter_by(
                patient_id=patient.id,
                doctor_id=doctor_record.id
            ).first()

            if not existing_appointment:
                new_appointment = Appointment(
                    patient_id=patient.id,
                    patient_name=patient.username,
                    email=patient.email,
                    doctor_id=doctor_record.id,
                    date=datetime.now().date(),
                    time=datetime.now().time(),
                    status='Booked'
                )
                db.session.add(new_appointment)
                created_count += 1
                print(f'✅ Created: {patient.username} → {doctor_user.username}')

print(f'\n✅ Created {created_count} new appointments')

if created_count > 0:
    db.session.commit()
    print('✅ All appointments saved to database')

print('\n=== FINAL APPOINTMENT LIST ===')
appointments = Appointment.query.all()
for apt in appointments:
    patient = User.query.get(apt.patient_id)
    doctor = Doctor.query.get(apt.doctor_id)
    if doctor:
        doctor_user = User.query.get(doctor.user_id)
        print(f'Patient {patient.username} ↔ Doctor {doctor_user.username} (Status: {apt.status})')