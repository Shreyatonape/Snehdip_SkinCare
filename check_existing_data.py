import sys
sys.path.append('.')
from app import app
from extensions import db
from models import User, Appointment, Doctor
from datetime import datetime
app.app_context().push()

print('=== CHECK EXISTING DATA ===')

# Check users
users = User.query.all()
print(f'Users ({len(users)}):')
for user in users:
    print(f'  - {user.username} ({user.role}) - ID: {user.id}')

# Check doctors table
doctors = Doctor.query.all()
print(f'\nDoctors table ({len(doctors)}):')
for doctor in doctors:
    print(f'  - {doctor.name} - User ID: {doctor.user_id}')

# Check existing appointments
appointments = Appointment.query.all()
print(f'\nExisting appointments ({len(appointments)}):')
for apt in appointments:
    print(f'  - Patient ID: {apt.patient_id} → Doctor ID: {apt.doctor_id} (Status: {apt.status})')

print('\n=== FIND VALID MAPPINGS ===')
# Find valid patient-doctor mappings
patients = User.query.filter_by(role='patient').all()
doctor_users = User.query.filter_by(role='doctor').all()

print(f'Patients: {len(patients)}')
print(f'Doctors: {len(doctor_users)}')

# Check which doctors exist in doctors table
valid_doctor_ids = [doctor.user_id for doctor in doctors]
print(f'Valid doctor IDs from doctors table: {valid_doctor_ids}')

# Create appointment if valid mapping exists
if patients and doctor_users:
    patient = patients[0]
    doctor_user = doctor_users[0]

    print(f'\nTrying to create appointment: {patient.username} (ID: {patient.id}) → {doctor_user.username} (ID: {doctor_user.id})')

    # Check if doctor exists in doctors table
    doctor_record = Doctor.query.filter_by(user_id=doctor_user.id).first()
    if doctor_record:
        print(f'✅ Doctor record found: {doctor_record.name} (User ID: {doctor_record.user_id})')

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
                doctor_id=doctor_record.id,  # Use doctor table ID
                date=datetime.now().date(),
                time=datetime.now().time(),
                status='Booked'
            )
            db.session.add(new_appointment)
            db.session.commit()
            print(f'✅ Created appointment successfully!')
        else:
            print(f'✅ Appointment already exists')
    else:
        print(f'❌ Doctor record not found for user {doctor_user.username} (ID: {doctor_user.id})')
        print('Need to create doctor record first')