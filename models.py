from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin
from datetime import datetime
from extensions import db

# -------------------------
# USERS TABLE (patients + doctors)
# -------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Doctor
    doctor_profile = db.relationship("Doctor", backref="user", foreign_keys="Doctor.user_id")

    def __repr__(self):
        return f"<User {self.username}>"
class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    specialization = db.Column(db.String(100))

    profile_image = db.Column(
        db.String(255),
        nullable=True,
        default="default_doctor.png"
    )


    def __repr__(self):
        return f"<Doctor {self.name}>"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    # 🔥 LINK TO USER (PATIENT)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    patient_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    # 🔥 LINK TO DOCTOR
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=True  # Made nullable to match current schema
    )

    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    issue = db.Column(db.Text)

    # 🔥 STATUS FLOW
    status = db.Column(
        db.String(20),
        default="Pending"
    )
    # Pending | Rejected | Completed

    # 🔥 REJECT REASON
    reject_reason = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # RELATIONS
    doctor = db.relationship("Doctor", backref="doctor_appointments")
    patient = db.relationship("User", backref="patient_appointments", foreign_keys="Appointment.patient_id")

    def __repr__(self):
        return f"<Appointment {self.id} - {self.patient_name}>"

class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),   # ✅ VERY IMPORTANT
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"), # optional
        nullable=True
    )
    diagnosis = db.Column(db.String(255))
    confidence = db.Column(db.Float)
    risk_level = db.Column(db.String(50))
    reason = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    prevention = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # ✅ Relationships
    patient = db.relationship("User", backref="patient_medical_records")
    doctor = db.relationship("Doctor", backref="doctor_medical_records")

    def __repr__(self):
        return f"<MedicalRecord {self.id} - {self.diagnosis}>"
class PatientRecord(db.Model):
    __tablename__ = "patient_record"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),   # ✅ VERY IMPORTANT
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"), # optional
        nullable=True
    )
    diagnosis = db.Column(db.String(255))
    confidence = db.Column(db.Float)
    risk_level = db.Column(db.String(50))
    reason = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    prevention = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

    doctor = db.relationship("Doctor", backref="availability")

    def __repr__(self):
        return f"<DoctorAvailability {self.id}>"
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)  # 'patient' or 'doctor'
    receiver_role = db.Column(db.String(20), nullable=False)  # 'patient' or 'doctor'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_receiver = db.Column(db.Boolean, default=False)

    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")

    def __repr__(self):
        return f"<Message {self.id}>"