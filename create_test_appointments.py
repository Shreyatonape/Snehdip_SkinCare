import sys
sys.path.append('.')
from app import app
from extensions import db
from models import User, Appointment
from datetime import datetime, date
app.app_context().push()

print('=== CREATE TEST APPOINTMENTS FOR MESSAGING ===')

# Get users
patients = User.query.filter_by(role='patient').all()
doctors = User.query.filter_by(role='doctor').all()

print(f'Found {len(patients)} patients and {len(doctors)} doctors')

# Create appointments for testing
if patients and doctors:
    # Create appointment between first patient and first doctor
    patient = patients[0]
    doctor = doctors[0]

    # Check if appointment already exists
    existing_appointment = Appointment.query.filter_by(
        patient_id=patient.id,
        doctor_id=doctor.id
    ).first()

    if not existing_appointment:
        new_appointment = Appointment(
            patient_id=patient.id,
            patient_name=patient.username,  # Required field
            email=patient.email,  # Required field
            doctor_id=doctor.id,
            date=date.today(),
            time=datetime.now().time(),
            status='Booked'
        )
        db.session.add(new_appointment)
        db.session.commit()
        print(f'✅ Created appointment: {patient.username} ↔ {doctor.username}')
    else:
        print(f'✅ Appointment already exists: {patient.username} ↔ {doctor.username}')

    # Create appointment between second patient and second doctor if available
    if len(patients) >= 2 and len(doctors) >= 2:
        patient2 = patients[1]
        doctor2 = doctors[1]

        existing_appointment2 = Appointment.query.filter_by(
            patient_id=patient2.id,
            doctor_id=doctor2.id
        ).first()

        if not existing_appointment2:
            new_appointment2 = Appointment(
                patient_id=patient2.id,
                patient_name=patient2.username,  # Required field
                email=patient2.email,  # Required field
                doctor_id=doctor2.id,
                date=date.today(),
                time=datetime.now().time(),
                status='Booked'
            )
            db.session.add(new_appointment2)
            db.session.commit()
            print(f'✅ Created appointment: {patient2.username} ↔ {doctor2.username}')
        else:
            print(f'✅ Appointment already exists: {patient2.username} ↔ {doctor2.username}')

print('\n=== APPOINTMENT MAPPINGS ===')
appointments = Appointment.query.all()
for apt in appointments:
    patient = User.query.get(apt.patient_id)
    doctor = User.query.get(apt.doctor_id)
    print(f'Patient {patient.username} ↔ Doctor {doctor.username} (Status: {apt.status})')

print('\n✅ Test appointments created successfully')
print('Patients can now message their assigned doctors')
print('Doctors can now message their assigned patients')