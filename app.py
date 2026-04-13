from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, abort

from dotenv import load_dotenv

from werkzeug.security import generate_password_hash, check_password_hash

from flask_cors import CORS

from flask_socketio import SocketIO, emit, join_room

from flask_login import login_required, current_user, LoginManager

from tensorflow.keras.preprocessing import image

from tensorflow.keras.models import load_model

from models import PatientRecord

from flask_migrate import Migrate
from flask import session
from datetime import datetime, date

import jwt

from itsdangerous import URLSafeTimedSerializer

from functools import wraps

import os

from extensions import db

from models import User, Doctor, Appointment, MedicalRecord, PatientRecord, DoctorAvailability, Message

# Import translation system

from utils.translator import translate_text
"""
load_dotenv()

app = Flask(__name__)

# Suppress TensorFlow warnings

import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable GPU if not needed

from tensorflow.keras.models import load_model

import tensorflow as tf

import numpy as np

# Set TensorFlow log level to reduce warnings

tf.get_logger().setLevel('ERROR')

# Model लोड करा एकदाच

try:

    model = load_model("ml/model.h5", compile=False)

    
except Exception as e:

    print(f"❌ Error loading model: {e}")

    model = None

# labels.json लोड करा

import json


with open("ml/labels.json", "r") as f:


    class_labels = json.load(f)


app.secret_key = os.getenv("SECRET_KEY", "mysecretkey")


serializer = URLSafeTimedSerializer(app.secret_key)


CORS(app)

"""

load_dotenv()

app = Flask(__name__)

# Set secret key for sessions
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# Suppress TensorFlow warnings
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable GPU if not needed

from tensorflow.keras.models import load_model
import tensorflow as tf
import numpy as np

# Set TensorFlow log level to reduce warnings
tf.get_logger().setLevel('ERROR')

   # -----------------------------
# LOAD NORMAL MODEL
# -----------------------------
try:
    normal_model = load_model("ml/ml/models/normal_model.h5", compile=False)
    print("✅ Normal model loaded")
except Exception as e:
    print(f"❌ Error loading normal model: {e}")
    normal_model = None

# -----------------------------
# LOAD DISEASE MODEL
# -----------------------------
try:
    disease_model = load_model("ml/ml/models/disease_model.h5", compile=False)
    print("✅ Disease model loaded")
except Exception as e:
    print(f"❌ Error loading disease model: {e}")
    disease_model = None

try:
    model = load_model("ml/model.h5", compile=False)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None


# labels.json लोड करा
import json
with open("ml/labels.json", "r") as f:
    class_labels = json.load(f) 
app.secret_key = os.getenv("SECRET_KEY", "mysecretkey")
serializer = URLSafeTimedSerializer(app.secret_key)
CORS(app)


DISEASE_NAME_MAP = {


    "akiec": "Actinic Keratoses",


    "bcc": "Basal Cell Carcinoma",


    "bkl": "Benign Keratosis",


    "df": "Dermatofibroma",


    "mel": "Melanoma",


    "nv": "Melanocytic Nevus",


    "vasc": "Vascular Lesion"


}


DISEASE_INFO = {


    "Actinic Keratoses": {


        "risk": "Medium",


        "reason": "Long-term sun exposure",


        "symptoms": "Rough, scaly patches on skin",


        "prevention": "Use sunscreen with SPF 30 or higher, avoid direct sun between 11 AM and 4 PM, wear protective clothing, and consult a doctor if rough patches appear"


    },


    "Basal Cell Carcinoma": {


        "risk": "High",


        "reason": "UV radiation damage",


        "symptoms": "Shiny bump or sore that doesn’t heal",


        "prevention": "Avoid prolonged sun exposure, use sunscreen regularly, and get regular skin checkups"


    },


    "Benign Keratosis": {


        "risk": "Low",


        "reason": "Age-related skin changes",


        "symptoms": "Waxy brown or black lesions",


        "prevention": "Maintain good skin hygiene and consult a doctor if unsure"


    },


    "Dermatofibroma": {


        "risk": "Low",


        "reason": "Minor skin injury",


        "symptoms": "Firm small bump",


        "prevention": "Avoid repeated skin injuries and scratching insect bites"


    },


    "Melanoma": {


        "risk": "Very High",


        "reason": "DNA damage from UV rays",


        "symptoms": "Irregular mole with color or size changes",


        "prevention": "Avoid sunburns, use sunscreen, and consult a doctor immediately if mole changes"


    },


    "Melanocytic Nevus": {


        "risk": "Low",


        "reason": "Benign mole",


        "symptoms": "Small brown or black spots",


        "prevention": "Monitor mole size, color or bleeding and protect skin from sunlight"


    },


    "Vascular Lesion": {


        "risk": "Low",


        "reason": "Blood vessel abnormality",


        "symptoms": "Red or purple skin marks",


        "prevention": "Avoid skin injury and consult a doctor if color or size changes"


    }


}


socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(


    "DATABASE_URL",


    "postgresql://postgres:pass%40123@localhost:5432/skincare_db"


)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


migrate = Migrate(app, db)


login_manager = LoginManager()


login_manager.login_view = "login_view"


login_manager.init_app(app)


# Make socketio available globally


app.socketio = socketio


# Register translation function globally in Jinja2


app.jinja_env.globals.update(translate=translate_text)


# ---------------------- Helper Functions ----------------------


def auto_reject_expired_appointments():


    """


    Automatically reject appointments that are past their date+time


    and still have 'Pending' status


    """


    current_time = datetime.utcnow()


    # Find expired pending appointments


    expired_appointments = Appointment.query.filter(


        Appointment.status == "Pending",


        db.or_(


            # Date is in the past


            Appointment.date < current_time.date(),


            # Date is today but time is past


            db.and_(


                Appointment.date == current_time.date(),


                Appointment.time < current_time.time()


            )


        )


    ).all()


    # Update expired appointments


    for appointment in expired_appointments:


        appointment.status = "Rejected"


        appointment.reject_reason = "Appointment time expired"


        print(f"Auto-rejected appointment {appointment.id} - expired")


    if expired_appointments:


        db.session.commit()


        print(f"Auto-rejected {len(expired_appointments)} expired appointments")


    return len(expired_appointments)


# ---------------------- Routes ----------------------


@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to avoid 500 errors"""
    return "", 204  # Return No Content


@app.route("/")


def index_view():


    return render_template("index.html")


@app.route("/set-language/<lang>")


def set_language_route(lang):


    """Set language in session and redirect back"""


    supported_languages = ['en', 'hi', 'mr']


    if lang in supported_languages:


        session['lang'] = lang


        flash(f"Language changed successfully!", "success")


    else:


        flash("Invalid language", "error")


    # Redirect back to previous page or home


    return redirect(request.referrer or url_for("index_view"))


@app.route("/register", methods=["GET", "POST"], endpoint="register")


def register_view():


    if request.method == "POST":


        username = request.form.get("username")


        email = request.form.get("email")


        password = request.form.get("password")


        # Check existing username


        if User.query.filter_by(username=username).first():


            flash("Username already exists. Please choose another.", "danger")


            return redirect(url_for("register"))


        # Check existing email


        if User.query.filter_by(email=email).first():


            flash("Email already exists. Please use another email.", "danger")


            return redirect(url_for("register"))


        hashed_password = generate_password_hash(


            password, method="pbkdf2:sha256", salt_length=8


        )


        try:


            # ✅ Create user


            new_user = User(


                username=username,


                email=email,


                password=hashed_password,


                role="patient"


            )


            db.session.add(new_user)


            db.session.commit()  # 🔥 user_id मिळवण्यासाठी


            flash("Registration successful! You can now login.", "success")


            return redirect(url_for("login_view"))


        except Exception as e:


            db.session.rollback()


            flash(f"Error: {str(e)}", "danger")


            return redirect(url_for("register"))


    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])


def login_view():


    if request.method == "POST":


        email = request.form.get("email")


        password = request.form.get("password")


        user = User.query.filter_by(email=email).first()


        if user and check_password_hash(user.password, password):


            session["user_id"] = user.id


            session["username"] = user.username


            session["role"] = user.role


            session["email"] = user.email


            flash("Login successful!", "success")


            if user.role == "doctor":


                return redirect(url_for("doctor_dashboard"))


            else:


                return redirect(url_for("patient_dashboard"))


        else:


            flash("Invalid email or password", "danger")


            return redirect(url_for("login_view"))


    return render_template("login.html")


@app.route("/create-admin")


def create_admin():


    from werkzeug.security import generate_password_hash


    admin = User(


        username="Snehal Kuldip Patil",


        email="admin@snehdip.com",


        password=generate_password_hash("admin2025"),


        role="doctor"


    )


    db.session.add(admin)


    db.session.commit()


    return "Admin Created Successfully!"


@app.route("/api/login", methods=["POST"])


def login():


    data = request.json


    email = data.get("email")


    password = data.get("password")


    # ✅ Hardcode for Dr. Sanskruti only


    if email == "yadavsanskruti17@gmail.com":


        if password == "12345":  # set a new temporary password


            token = create_access_token(identity={"email": email, "role": "doctor"})


            return jsonify({"token": token, "role": "doctor"})


        else:


            return jsonify({"message": "Incorrect password"}), 401


    # other users...


    return jsonify({"message": "Invalid credentials"}), 401


@app.route('/doctor/registered_patients')


def doctor_registered_patients():


    if 'role' in session and session['role']=='doctor':


        patients = User.query.filter_by(role='patient').all()


        return render_template('doctor_dashboard.html', registered_patients=patients)


    else:


        return redirect(url_for('login_view'))


@app.route("/logout")


def logout_view():


    session.clear()


    flash("Logged out successfully!", "info")


    return redirect(url_for("index_view"))


@app.route("/api/appointments", methods=["GET"])


def patient_api_appointments():   # ✅ renamed function only


    # Validate session first


    if "email" not in session or session.get("role") != "patient":


        return jsonify([]), 401


    # Get patient user


    patient_user = User.query.filter_by(email=session.get("email")).first()


    if not patient_user:


        return jsonify([]), 401


    # Get ALL patient's appointments (all statuses) using patient_id


    appointments = Appointment.query.filter_by(patient_id=patient_user.id).order_by(Appointment.created_at.desc()).all()


    data = []


    for a in appointments:


       doctor_obj = Doctor.query.get(a.doctor_id)


    data.append({


            "id": a.id,


            "patientName": a.patient_name,


            "doctorName": doctor_obj.name if doctor_obj else "Unknown",


            "date": a.date.isoformat(),


            "time": a.time.strftime("%H:%M") if a.time else None,


            "issue": a.issue,


            "status": a.status,


            "completed_at": a.completed_at.isoformat() if a.completed_at else None,


            "reject_reason": a.reject_reason


        })


    return jsonify(data)


@app.route("/api/appointments", methods=["POST"])


@login_required


def book_appointment():


    try:


        data = request.get_json()


        appointment = Appointment(


            patient_id=session["user_id"],


            patient_name=data["name"],


            email=data["email"],


            doctor_id=int(data["doctorId"]),  # 🔥 VERY IMPORTANT


            date=data["date"],


            time=data["time"],


            issue=data["issue"],


            status="Pending"


        )


        db.session.add(appointment)


        db.session.commit()   # 🔥 THIS WAS MISSING


        return jsonify({"message": "Appointment booked successfully"}), 201


    except Exception as e:


        db.session.rollback()


        print("❌ Appointment error:", e)


        return jsonify({"error": str(e)}), 500


# ---------------------- Dashboards ----------------------


@app.route("/doctor/dashboard")


def doctor_dashboard():


    if session.get("role") != "doctor":


        flash("Unauthorized access!", "danger")


        return redirect(url_for("login_view"))


    # ✅ Only fetch registered patients


    registered_patients = User.query.filter_by(role="patient").all()


    return render_template(


        "doctor_dashboard.html",


        registered_patients=registered_patients


    )


@app.route("/doctor/records")


def doctor_records_view():


    try:


        if session.get("role") != "doctor":


            return redirect(url_for("login_view"))


        patient_id = request.args.get("patient_id")


        # If patient_id missing -> redirect automatically


        if not patient_id:


            first_patient = User.query.filter_by(role="patient").first()


            if first_patient:


                return redirect(url_for(


                    "doctor_records_view",


                    patient_id=first_patient.id


                ))


            else:


                return "No patients found"


        # Convert patient_id to integer and validate


        try:


            patient_id = int(patient_id)


        except (ValueError, TypeError):


            return "Invalid patient ID"


        # Get patient and check if exists


        patient = User.query.get(patient_id)


        if not patient:


            # Patient not found, redirect to first available patient


            first_patient = User.query.filter_by(role="patient").first()


            if first_patient:


                return redirect(url_for(


                    "doctor_records_view",


                    patient_id=first_patient.id


                ))


            else:


                return "No patients found"


        # Check if the user is actually a patient


        if patient.role != "patient":


            # User is not a patient, redirect to first available patient


            first_patient = User.query.filter_by(role="patient").first()


            if first_patient:


                return redirect(url_for(


                    "doctor_records_view",


                    patient_id=first_patient.id


                ))


            else:


                return "No patients found"


        return render_template(


            "doctor_records.html",


            patient_name=patient.username,


            patient_id=patient_id


        )


    except Exception as e:


        print(f"ERROR in doctor_records_view: {str(e)}")

        return "Error loading patient records", 500


@app.route("/doctor/profile")


def doctor_profile_view():


    if "user_id" not in session or session.get("role") != "doctor":


        return redirect(url_for("login_view"))


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    # ✅ AUTO CREATE DOCTOR PROFILE IF NOT EXISTS


    if not doctor:


        user = User.query.get(session["user_id"])


        doctor = Doctor(


            user_id=user.id,


            name=user.username,


            email=user.email


        )


        db.session.add(doctor)


        db.session.commit()


    return render_template("doctor_profile.html", doctor=doctor)


from werkzeug.utils import secure_filename  # ✅ REQUIRED


@app.route("/doctor/update_profile", methods=["POST"])


def update_profile():


    if "user_id" not in session or session.get("role") != "doctor":


        flash("Unauthorized access", "danger")


        return redirect(url_for("login_view"))


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    if not doctor:


        user = User.query.get(session["user_id"])


        doctor = Doctor(


            user_id=user.id,


            name=user.username,


            email=user.email


        )


        db.session.add(doctor)


    doctor.name = request.form.get("name")


    doctor.email = request.form.get("email")


    doctor.specialization = request.form.get("specialization")


    # ✅ IMAGE UPLOAD


    file = request.files.get("profile_image")


    if file and file.filename:


        upload_folder = os.path.join(app.root_path, "static/uploads/doctors")


        os.makedirs(upload_folder, exist_ok=True)  # ✅ CREATE FOLDER


        filename = secure_filename(file.filename)


        file.save(os.path.join(upload_folder, filename))


        doctor.profile_image = filename  # ✅ CORRECT PLACE


    db.session.commit()


    flash("Profile updated successfully ✅", "success")


    return redirect(url_for("doctor_profile_view"))


@app.route("/patient/dashboard")


def patient_dashboard():


    if session.get("role") != "patient":


        flash("Unauthorized access!", "danger")


        return redirect(url_for("login_view"))


    # Get patient user from session


    patient_user = User.query.filter_by(email=session.get("email")).first()


    if not patient_user:


        flash("User session invalid", "danger")


        return redirect(url_for("login_view"))


    # Fetch ALL patient's appointments (all statuses) using patient_id


    appointments = Appointment.query.filter_by(patient_id=patient_user.id).order_by(Appointment.created_at.desc()).all()


    # Fetch doctor names for each appointment


    appointments_data = []


    for a in appointments:


        doctor = Doctor.query.get(a.doctor_id)


        appointments_data.append({


            "id": a.id,


            "doctor_name": doctor.name if doctor else "Unknown",


            "date": a.date.strftime("%Y-%m-%d"),


            "time": a.time.strftime("%H:%M") if a.time else "N/A",


            "issue": a.issue,


            "status": a.status,


            "completed_at": a.completed_at.strftime("%Y-%m-%d %H:%M") if a.completed_at else None,


            "reject_reason": a.reject_reason


        })


    print("PATIENT APPOINTMENTS:", appointments_data)  # 🔥 DEBUG


    return render_template(


        "patient_dashboard.html",


        appointments=appointments_data


    )


@app.route("/patient/records")


def patient_records_view():


   # optional: check session role


    if session.get("role") != "patient":


        flash("Unauthorized", "danger")


        return redirect(url_for("login_view"))


    return render_template("patient_records.html")


@app.route('/api/records')
def get_records():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        role = session.get("role")

        result = []

        if role == "patient":
            patient_id = session["user_id"]

        elif role == "doctor":
            patient_id = request.args.get("patient_id")
            if not patient_id:
                return jsonify([])

        else:
            return jsonify([]), 403

        # Convert patient_id to integer if it's a string
        try:
            patient_id = int(patient_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid patient_id parameter"}), 400

        records = MedicalRecord.query.filter_by(patient_id=patient_id).all()

        for r in records:
            try:
                result.append({
                    "id": r.id,
                    "image_path": url_for('static', filename=r.image_path) if r.image_path else None,
                    "diagnosis": r.diagnosis,
                    "confidence": r.confidence,
                    "risk_level": r.risk_level,
                    "reason": r.reason,
                    "symptoms": r.symptoms,
                    "prevention": r.prevention,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
                })
            except Exception as e:
                print(f"Error processing record {r.id}: {str(e)}")
                continue

        return jsonify(result)

    except Exception as e:
        print(f"ERROR in get_records: {str(e)}")
        return jsonify({"error": "Failed to load records"}), 500

@app.route("/api/records/<int:record_id>", methods=["DELETE"])


def delete_record(record_id):


    if "user_id" not in session or session.get("role") != "doctor":


        return jsonify({"error": "Unauthorized"}), 401


    record = MedicalRecord.query.get(record_id)


    if not record:


        return jsonify({"error": "Record not found"}), 404


    db.session.delete(record)


    db.session.commit()


    return jsonify({"success": True})


@app.route("/api/patient/records/<int:record_id>", methods=["DELETE"])


def delete_patient_record(record_id):


    # ✅ Patient must be logged in


    if "user_id" not in session or session.get("role") != "patient":


        return jsonify({"error": "Unauthorized"}), 401


    # ✅ Get record


    record = MedicalRecord.query.get(record_id)


    if not record:


        return jsonify({"error": "Record not found"}), 404


    # ✅ Patient can delete ONLY their own record


    if record.patient_id != session["user_id"]:


        return jsonify({"error": "Forbidden"}), 403


    db.session.delete(record)


    db.session.commit()


    return jsonify({"success": True})


@app.route("/doctor/delete-user/<int:user_id>", methods=["DELETE"])


def delete_user(user_id):
    try:
        if session.get("role") != "doctor":
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        if user.role == "doctor":
            return jsonify({"success": False, "message": "Cannot delete doctor"}), 400

        # Check if user has related records that need to be deleted first
        from models import Appointment, MedicalRecord, Message, PatientRecord, DoctorAvailability

        # Delete related appointments
        appointments = Appointment.query.filter_by(patient_id=user_id).all()
        for appointment in appointments:
            db.session.delete(appointment)

        # Delete related medical records
        medical_records = MedicalRecord.query.filter_by(patient_id=user_id).all()
        for record in medical_records:
            db.session.delete(record)

        # Delete related patient records
        patient_records = PatientRecord.query.filter_by(patient_id=user_id).all()
        for record in patient_records:
            db.session.delete(record)

        # Delete related messages (both as sender and receiver)
        messages_as_sender = Message.query.filter_by(sender_id=user_id).all()
        for message in messages_as_sender:
            db.session.delete(message)

        messages_as_receiver = Message.query.filter_by(receiver_id=user_id).all()
        for message in messages_as_receiver:
            db.session.delete(message)

        # Delete the user
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error deleting user: {str(e)}"}), 500


# ---------------------- Placeholder Pages ----------------------


@app.route("/upload")


def upload_view():


    return render_template("upload.html")


@app.route("/chat")


def chat_view():


    return render_template("patient_doctor_chat.html")


@app.route("/about")


def about_view():


    return render_template("about.html")


@app.route("/hospitals")


def hospitals_view():


    return render_template("hospitals.html")


@app.route("/online")


def online_view():


    return render_template("online.html")


# ---------------------- API Predict Route ----------------------

"""
@login_required


@app.route("/api/predict", methods=["POST"])


def predict():


    if model is None:


        return jsonify({"success": False, "error": "Model not available"})


    file = request.files.get("file")


    if not file:


        return jsonify({"success": False, "error": "No file uploaded"})


    # ✅ Save image


    os.makedirs("static/uploads", exist_ok=True)


    filename = file.filename


    file_save_path = os.path.join("static", "uploads", filename)


    file.save(file_save_path)


    image_path = f"uploads/{filename}"


    # ✅ Preprocess image


    img = image.load_img(file_save_path, target_size=(128, 128))


    img_array = image.img_to_array(img)


    img_array = np.expand_dims(img_array, axis=0) / 255.0


    # ✅ Predict


    pred = model.predict(img_array)[0]   # 🔥 IMPORTANT [0]


    confidence = float(np.max(pred))


    class_idx = int(np.argmax(pred))


    # ✅ Safe Top-2 difference check


    if len(pred) > 1:


        sorted_probs = np.sort(pred)


        difference = float(sorted_probs[-1] - sorted_probs[-2])


    else:


        difference = confidence  # fallback safety


    # 🔥 Confidence + difference threshold


    if confidence < 0.45 or difference < 0.15:


        return jsonify({


            "success": True,


            "disease": "Uncertain / Not a Skin Disease Image",


            "confidence": confidence * 100,


            "risk_level": "Low",


            "reason": "Model is not confident. Please upload a clear skin lesion image.",


            "symptoms": "Not Available",


            "prevention": "Upload proper skin disease image."


        })


    # ✅ Get disease info


    class_code = class_labels[str(class_idx)]


    disease_name = DISEASE_NAME_MAP.get(class_code, "Unknown")


    info = DISEASE_INFO.get(disease_name, {})


    # ✅ Save record for patient


    if "user_id" in session and session.get("role") == "patient":


        record = MedicalRecord(


            patient_id=session["user_id"],


            doctor_id=None,


            diagnosis=disease_name,


            confidence=confidence * 100,


            risk_level=info.get("risk"),


            reason=info.get("reason"),


            symptoms=info.get("symptoms"),


            prevention=info.get("prevention"),


            image_path=image_path


        )


        db.session.add(record)


        db.session.commit()


    # ✅ Final Response


    return jsonify({


        "success": True,


        "disease": disease_name,


        "confidence": confidence * 100,


        "risk_level": info.get("risk", "Not Available"),


        "reason": info.get("reason", "Not Available"),


        "symptoms": info.get("symptoms", "Not Available"),


        "prevention": info.get("prevention", "Not Available")


    })
"""


import cv2
def is_skin_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return False

    img = cv2.resize(img, (224, 224))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Skin color range (basic)
    lower = np.array([0, 30, 50])
    upper = np.array([35, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    skin_ratio = np.sum(mask > 0) / (224 * 224)
 # ✅ Texture check (important!)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = np.var(gray)

    print("Skin Ratio:", skin_ratio, "Variance:", variance)  # debug

    # ✅ FINAL LOGIC
    return skin_ratio > 0.08 and variance > 40


@login_required
@app.route("/api/predict", methods=["POST"])
def predict():

    if normal_model is None or model is None:
        return jsonify({"success": False, "error": "Model not available"})
        
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "error": "No file uploaded"})

    
    # ✅ Save image
    os.makedirs("static/uploads", exist_ok=True)
    filename = file.filename
    file_save_path = os.path.join("static", "uploads", filename)
    file.save(file_save_path)
    image_path = f"uploads/{filename}"

# ✅ HERE
    if not is_skin_image(file_save_path):
        return jsonify({
            "success": True,
            "disease": "Invalid Image",
            "confidence": 0,
            "risk_level": "Unknown",
            "reason": "Uploaded image is not a skin image",
            "symptoms": "Not applicable",
            "prevention": "Please upload a valid skin image"
        })
    
    # ✅ Preprocess image (FIXED SIZE)
    img = image.load_img(file_save_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    # -----------------------------
    # STEP 1: NORMAL MODEL
    # -----------------------------
    normal_pred = normal_model.predict(img_array)[0][0]

    if normal_pred > 0.7:
        return jsonify({
            "success": True,
            "disease": "Normal Skin",
            "confidence": float(normal_pred * 100),
            "risk_level": "Low",
            "reason": "No visible skin disease detected",
            "symptoms": "Healthy skin",
            "prevention": "Maintain regular skincare routine"
        })

    # -----------------------------
    # STEP 2: DISEASE MODEL
    # -----------------------------
    IMG_SIZE = model.input_shape[1]

    img_disease = image.load_img(file_save_path, target_size=(IMG_SIZE, IMG_SIZE))
    img_disease_array = image.img_to_array(img_disease)
    img_disease_array = np.expand_dims(img_disease_array, axis=0) / 255.0

    pred = model.predict(img_disease_array)[0]

    confidence = float(np.max(pred))
    class_idx = int(np.argmax(pred))

    class_code = class_labels[str(class_idx)]
    disease_name = DISEASE_NAME_MAP.get(class_code, "Unknown")
    info = DISEASE_INFO.get(disease_name, {})

    # ✅ Save record
    if "user_id" in session and session.get("role") == "patient":
        record = MedicalRecord(
            patient_id=session["user_id"],
            doctor_id=None,
            diagnosis=disease_name,
            confidence=confidence * 100,
            risk_level=info.get("risk"),
            reason=info.get("reason"),
            symptoms=info.get("symptoms"),
            prevention=info.get("prevention"),
            image_path=image_path
        )
        db.session.add(record)
        db.session.commit()
    return jsonify({
        "success": True,
        "disease": disease_name,
        "confidence": confidence * 100,
        "risk_level": info.get("risk", "Not Available"),
        "reason": info.get("reason", "Not Available"),
        "symptoms": info.get("symptoms", "Not Available"),
        "prevention": info.get("prevention", "Not Available")
    })




@app.route("/api/chatbot/ask", methods=["POST"])


def ask_chatbot():


    data = request.get_json()


    if not data or "message" not in data:


        return jsonify({"reply": "⚠️ Invalid request"}), 400


    msg = data["message"].lower().strip()


    # Basic intents


    greetings = ["hi", "hello", "hey", "good morning", "good evening"]


    thanks = ["thanks", "thank you", "thx"]


    # Responses


    if any(word in msg for word in greetings):


        reply = (


            "Hello! 👋 I am Doctor Bot 🤖\n"


            "You can ask me about skin problems, image upload, appointments, or hospitals."


        )


    elif any(word in msg for word in thanks):


        reply = "You're welcome! 😊 Take care of your skin 💖"


    # 🔹 Skin problems (medical)


    elif any(word in msg for word in ["rash", "red", "itch", "itching"]):


        reply = "It looks like skin irritation. Keep the area clean and avoid scratching."


    elif any(word in msg for word in ["acne", "pimples"]):


        reply = "This may be acne. Wash your face twice daily and avoid oily food."


    elif "eczema" in msg:


        reply = "This may be eczema. Keep your skin well moisturized."


    elif "psoriasis" in msg:


        reply = "Psoriasis usually requires medical treatment. Please consult a dermatologist."


    elif "fungal" in msg or "ringworm" in msg:


        reply = "This may be a fungal infection. Keep the affected area clean and dry."


    elif "allergy" in msg:


        reply = "This may be a skin allergy. Stop using new cosmetic products."


    elif "dry skin" in msg:


        reply = "For dry skin, use a good moisturizer and drink plenty of water."


    elif "oily skin" in msg:


        reply = "For oily skin, use an oil-free face wash."


    elif "dark spots" in msg or "pigmentation" in msg:


        reply = "For pigmentation, using sunscreen daily is very important."


    elif "hair fall" in msg or "hair loss" in msg:


        reply = "For hair fall, maintain a healthy diet and consult a dermatologist."


    # 🔹 Project features


    elif "upload" in msg or "image" in msg:


        reply = "Go to the Upload page and upload your skin image."


    elif "prediction" in msg or "result" in msg:


        reply = "After uploading the image, the AI will give you a disease prediction."


    elif "appointment" in msg or "book" in msg:


        reply = "To book an appointment, please visit the Contact Doctor page."


    elif "doctor" in msg:


        reply = "You can find available dermatologists in the Hospital section."


    elif "hospital" in msg:


        reply = "The Hospital page provides information about nearby hospitals and doctors."


    elif "medicine" in msg or "buy" in msg:


        reply = "You can purchase medicines from the Buy Medicine section."


    elif "report" in msg:


        reply = "Your medical reports are saved in your dashboard."


    elif "login" in msg or "register" in msg:


        reply = "Login or registration is required to access all features."


    elif "video call" in msg or "meet" in msg:


        reply = "You can start a video call after your appointment is confirmed."


    # 🔹 Fallback
    # 🔐 Validation Help (Patient)

    elif "validation" in msg or "form rules" in msg:
        reply = (
            "Form Validation Rules:\n"
            "✔ Username should not be empty\n"
            "✔ Email must be valid (example@gmail.com)\n"
            "✔ Password must be at least 6 characters\n"
            "✔ All fields are required"
        )

    elif "email validation" in msg or "invalid email" in msg:
        reply = (
            "Email Validation:\n"
            "✔ Enter a valid email like example@gmail.com\n"
            "❌ Do not use spaces or invalid format"
        )

    elif "password validation" in msg or "password rules" in msg:
        reply = (
            "Password Rules:\n"
            "✔ Minimum 6 characters required\n"
            "✔ Use letters and numbers for better security"
        )

    elif "username validation" in msg:
        reply = (
            "Username Rules:\n"
            "✔ Username should not be empty\n"
            "✔ Avoid special characters\n"
            "✔ Choose a simple and unique name"
        )

    elif "form error" in msg or "why form not submitting" in msg:
        reply = (
            "Form not submitting?\n"
            "✔ Check all fields are filled\n"
            "✔ Make sure email format is correct\n"
            "✔ Password should meet requirements\n"
            "✔ Check internet connection"
        )

    # 📝 Patient Registration Form Help

    elif "registration form" in msg or "register form" in msg:
        reply = (
            "Patient Registration Form includes:\n"
            "1️⃣ Username\n"
            "2️⃣ Email\n"
            "3️⃣ Password\n"
            "4️⃣ Role (Select Patient)\n\n"
            "Fill all details correctly and click Register."
        )

    elif "what to fill in registration" in msg:
        reply = (
            "In Registration Form:\n"
            "✔ Username → your name (e.g. Shreya)\n"
            "✔ Email → valid email (example@gmail.com)\n"
            "✔ Password → minimum 6 characters\n"
            "✔ Role → select Patient\n"
        )

    elif "how to fill register form" in msg:
        reply = (
            "Steps to fill Registration Form:\n"
            "1️⃣ Enter Username\n"
            "2️⃣ Enter Email\n"
            "3️⃣ Enter Password\n"
            "4️⃣ Select Patient role\n"
            "5️⃣ Click Register button\n"
        )

    elif "registration error" in msg or "not registering" in msg:
        reply = (
            "If registration is not working:\n"
            "✔ Check all fields are filled\n"
            "✔ Email should be valid\n"
            "✔ Password must be at least 6 characters\n"
            "✔ Username/Email should not already exist\n"
        )

    elif "after registration" in msg:
        reply = (
            "After successful registration:\n"
            "1️⃣ Go to Login page\n"
            "2️⃣ Enter your email and password\n"
            "3️⃣ Access your Patient Dashboard\n"
        )

    elif (
    "how to register" in msg or
    "how to make registration" in msg or
    "registration process" in msg or
    "create account" in msg or
    "sign up" in msg or
    "register" in msg
):
        reply = (
            "To create a Patient account:\n"
            "1️⃣ Go to Register page\n"
            "2️⃣ Enter username, email, password\n"
            "3️⃣ Click Register button\n"
            "4️⃣ Then login using your credentials"
        )

    elif "registration" in msg and ("require" in msg or "required" in msg or "need" in msg):
        reply = (
            "Yes ✅ Registration is required.\n\n"
            "You need to create an account to:\n"
            "✔ Upload images\n"
            "✔ Get predictions\n"
            "✔ Book appointments\n"
            "✔ View reports"
        )
    else:


        reply = (


            "I'm not sure I understood that 🤔\n"


            "Please ask about skin problems, image upload, appointments, or doctors."


        )


    return jsonify({"reply": reply})


@app.route("/contact", methods=["GET", "POST"])


def contact_view():


    if request.method == "POST":


        patient_name = request.form.get("patientName")


        email = request.form.get("email")


        doctor_id = int(request.form.get("doctorId"))


        date_val = request.form.get("date")


        time_val = request.form.get("time")


        issue = request.form.get("issue")


        # Get doctor by user_id (since frontend sends user_id)


        doctor = Doctor.query.filter_by(user_id=doctor_id).first()


        if not doctor:


            flash("Doctor not found", "danger")

            return redirect(url_for("contact_view"))

        # Get patient user ID from session

        patient_user = User.query.filter_by(email=session.get("email")).first()

        if not patient_user:


            flash("User session invalid", "danger")

            return redirect(url_for("login_view"))

        appointment = Appointment(

            patient_id=patient_user.id,   # Use actual user ID

            patient_name=patient_name,


            email=email,


            doctor_id=doctor.id,             # ✅ doctors.id


            date=date_val,


            time=time_val,


            issue=issue,


            status="Pending"


        )


        db.session.add(appointment)


        db.session.commit()


        flash("Appointment booked successfully ✅", "success")


        return redirect(url_for("contact_view"))


    # 🔥 SEND DOCTOR LIST with user_id for frontend


    doctors = Doctor.query.all()


    # Add user_id to each doctor for frontend compatibility


    doctor_list = []


    for doctor in doctors:


        doctor_list.append({


            'id': doctor.id,


            'user_id': doctor.user_id,


            'name': doctor.name,


            'specialization': doctor.specialization


        })


    return render_template("contact.html", doctors=doctor_list)


@app.route("/doctor/appointments")


def doctor_appointments_page():


    if session.get("role") != "doctor":


        flash("Unauthorized access!", "danger")


        return redirect(url_for("login_view"))


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first_or_404()


    appointments = Appointment.query.filter_by(


        doctor_id=doctor.id


    ).order_by(Appointment.created_at.desc()).all()
    return render_template(
        "doctor_appointments.html",
        appointments=appointments,
        doctor=doctor
    )


@login_manager.user_loader


def load_user(user_id):


    return User.query.get(int(user_id))


@app.route("/home-remedies")


def home_remedies_view():


    return render_template("HomeRemidies.html")


@app.route("/doctor/users")


def doctor_all_users():


    if session.get("role") != "doctor":


        flash("Unauthorized access!", "danger")


        return redirect(url_for("login_view"))

    users = User.query.order_by(User.created_at.desc()).all()


    return render_template(


        "doctor_users.html",


        users=users


    )


# ---------------------- JWT Token Decorator ----------------------


def token_required(f):


    """JWT authentication decorator for API endpoints"""


    @wraps(f)


    def decorated(*args, **kwargs):


        token = None


        # Get token from Authorization header


        if 'Authorization' in request.headers:


            auth_header = request.headers['Authorization']


            try:


                token = auth_header.split(" ")[1]  # Bearer <token>


            except IndexError:


                return jsonify({"error": "Invalid token format"}), 401


        if not token:


            return jsonify({"error": "Token is missing"}), 401


        try:


            # Decode JWT token


            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])


            # Support both payload.id and payload.user_id for frontend compatibility


            current_user_id = payload.get('user_id') or payload.get('id')


            current_role = payload.get('role')


            if not current_user_id or not current_role:


                return jsonify({"error": "Invalid token payload"}), 401


            # Add to request context


            request.current_user_id = current_user_id


            request.current_role = current_role


            return f(*args, **kwargs)


        except jwt.ExpiredSignatureError:


            return jsonify({"error": "Token has expired"}), 401


        except jwt.InvalidTokenError:


            return jsonify({"error": "Invalid token"}), 401


    return decorated


# ---------------------- Simple Role-based Decorator ----------------------


def role_required(*allowed_roles):


    """Role-based authentication decorator"""


    def decorator(f):


        @wraps(f)


        def decorated(*args, **kwargs):


            if 'role' not in session:


                return jsonify({"error": "Authentication required"}), 401


            if session['role'] not in allowed_roles:


                return jsonify({"error": "Access denied"}), 403


            return f(*args, **kwargs)


        return decorated


    return decorator


# ---------------------- Doctor Management Routes ----------------------


@app.route("/api/admin/doctors", methods=["GET"])


@role_required('doctor')


def get_admin_doctors():


    """Get list of all doctors"""


    try:


        doctors = User.query.filter_by(role="doctor").all()


        doctors_list = []


        for doctor in doctors:


            doctors_list.append({


                "id": doctor.id,


                "username": doctor.username,


                "email": doctor.email,


                "created_at": doctor.created_at.isoformat() if doctor.created_at else None


            })


        return jsonify({


            "success": True,


            "doctors": doctors_list


        })


    except Exception as e:


        print(f"Error getting doctors: {e}")


        return jsonify({"error": "Failed to load doctors"}), 500


# ---------------------- SocketIO Events ----------------------


chat_history = {}


@socketio.on("connect")


def on_connect():


    print("CLIENT CONNECTED:", request.sid)


    emit("system_message", {"message": "Connected to chat server!"})


@socketio.on("disconnect")


def on_disconnect():


    print("CLIENT DISCONNECTED:", request.sid)


@socketio.on("join")


def handle_join(data):


    room = data.get("room")


    user = data.get("user", "Anonymous")


    role = data.get("role", "user")


    print(f"USER {user} ({role}) JOINING ROOM: {room}")


    join_room(room)


    # Notify others in room


    emit("system_message", {


        "message": f"{user} ({role}) joined the chat"


    }, room=room, include_self=False)


    # Send confirmation


    emit("system_message", {


        "message": f"Joined room: {room}"


    })


@socketio.on("message")


def handle_message(data):


    room = data.get("room")


    sender = data.get("sender", "unknown")


    message = data.get("message", "")


    user = data.get("user", "Anonymous")


    timestamp = data.get("timestamp", datetime.now().isoformat())


    if not room or not message:


        return


    # Create message entry


    entry = {


        "sender": sender,


        "message": message,


        "user": user,


        "timestamp": timestamp


    }


    # Store in chat history


    chat_history.setdefault(room, []).append(entry)


    # Broadcast to room


    emit("new_message", entry, room=room)


    print(f"MESSAGE in {room}: {user} ({sender}): {message}")


@socketio.on("leave")


def handle_leave(data):


    room = data.get("room")


    user = data.get("user", "Anonymous")


    leave_room(room)


    emit("system_message", {


        "message": f"{user} left the chat"


    }, room=room)


@app.route("/doctor/chat")


def doctor_chat():


    if session.get("role") != "doctor":


        return redirect(url_for("login_view"))


    patients = User.query.filter_by(role="patient").all()


    patient_id = request.args.get("patient_id")


    patient_name = request.args.get("patient_name")


    return render_template(


        "doctor_chat.html",


        patients=patients,


        patient_id=patient_id,


        patient_name=patient_name


    )


@app.route("/patient/chat")


def patient_chat():


    if session.get("role") != "patient":


        return redirect(url_for("login_view"))


    # Get patient user from session


    patient_user = User.query.filter_by(email=session.get("email")).first()


    if not patient_user:


        flash("User session invalid", "danger")


        return redirect(url_for("login_view"))


    print(f"DEBUG: Patient user found: {patient_user.id if patient_user else 'None'}")


    print(f"DEBUG: Session email: {session.get('email')}")


    # Get patient's latest appointment using patient_id (not email)


    appointment = Appointment.query.filter_by(


        patient_id=patient_user.id


    ).order_by(Appointment.id.desc()).first()


    print(f"DEBUG: Appointment found: {appointment.id if appointment else 'None'}")


    # If no appointment, show available doctors instead of blocking


    if not appointment:


        # Get all doctors for patient to choose from


        doctors = Doctor.query.all()


        return render_template(


            "patient_chat.html",


            doctors=doctors,


            show_doctor_selection=True


        )


    return render_template(


        "patient_chat.html",


        appointment_id=appointment.id,


        doctor_name=Doctor.query.get(appointment.doctor_id).name


    )


@app.route("/doctor/chat-patients")


def doctor_chat_patients():


    if session.get("role") != "doctor":


        return redirect(url_for("login_view"))


    patients = User.query.filter_by(role="patient").all()


    return render_template(


        "doctor_chat_patients.html",


        patients=patients


    )


@app.route("/api/doctor/appointments/<int:appointment_id>/complete", methods=["PATCH"])


def complete_appointment(appointment_id):


    # 🔐 ensure doctor logged in via session


    if "user_id" not in session or session.get("role") != "doctor":


        return jsonify({"error": "Unauthorized - Doctor access required"}), 401


    # Get appointment


    appointment = Appointment.query.get_or_404(appointment_id)


    # Get doctor from session


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    if not doctor:


        return jsonify({"error": "Doctor profile not found"}), 404


    # 🔐 SECURITY CHECK - ensure doctor owns this appointment


    if appointment.doctor_id != doctor.id:


        return jsonify({"error": "Forbidden - Not your appointment"}), 403


    # Check if already completed


    if appointment.status == "Completed":


        return jsonify({"error": "Already completed"}), 400


    # Update appointment


    appointment.status = "Completed"


    appointment.completed_at = datetime.utcnow()


    db.session.commit()


    return jsonify({


        "success": True,


        "appointment_id": appointment.id,


        "status": "Completed",


        "completed_at": appointment.completed_at.isoformat()


    })


@app.route("/api/doctor/appointments/<int:appointment_id>/reject", methods=["PATCH"])


def reject_appointment(appointment_id):


    # 🔐 ensure doctor logged in via session


    if "user_id" not in session or session.get("role") != "doctor":


        return jsonify({"error": "Unauthorized - Doctor access required"}), 401


    # Get appointment


    appointment = Appointment.query.get_or_404(appointment_id)


    # Get doctor from session


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    if not doctor:


        return jsonify({"error": "Doctor profile not found"}), 404


    # 🔐 SECURITY CHECK - ensure doctor owns this appointment


    if appointment.doctor_id != doctor.id:


        return jsonify({"error": "Forbidden - Not your appointment"}), 403


    # Get rejection reason from request


    data = request.get_json() or {}


    reason = data.get("reason", "Rejected by doctor")


    # Update appointment


    appointment.status = "Rejected"


    appointment.reject_reason = reason


    db.session.commit()


    return jsonify({
        "success": True,
        "appointment_id": appointment.id,
        "status": "Rejected",
        "reject_reason": appointment.reject_reason
    })
@app.route("/api/doctor/appointments/<int:appointment_id>/delete", methods=["DELETE"])
def delete_appointment(appointment_id):
    try:
        if session.get("role") != "doctor":
            return jsonify({"error": "Unauthorized - Doctor access required"}), 401

        # ensure doctor owns this appointment
        doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()
        if not doctor:
            return jsonify({"error": "Doctor profile not found"}), 404

        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        # ensure doctor owns this appointment
        if appointment.doctor_id != doctor.id:
            return jsonify({"error": "Forbidden - Not your appointment"}), 403

        print(f"Attempting to delete appointment: {appointment.id}")
        db.session.delete(appointment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Appointment deleted successfully",
            "appointment_id": appointment_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete appointment: {str(e)}"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route("/api/doctor/appointments/<int:appointment_id>/update", methods=["PATCH"])
def update_appointment(appointment_id):
    if session.get("role") != "doctor":
        return {"error": "Unauthorized"}, 403


    data = request.get_json()


    appointment = Appointment.query.get_or_404(appointment_id)


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    # 🔐 SECURITY CHECK


    if appointment.doctor_id != doctor.id:


        return {"error": "Forbidden"}, 403


    status = data.get("status")


    if status == "Rejected":


        appointment.status = "Rejected"


        appointment.reject_reason = data.get(


            "reason", "You did not come within the appointment time"


        )


    elif status == "Completed":


        appointment.status = "Completed"


        appointment.completed_at = datetime.utcnow()


    else:


        return {"error": "Invalid status"}, 400


    db.session.commit()


    return {"success": True}


@app.route("/api/doctor/appointments", methods=["GET"])


def doctor_api_appointments():


    # 🔐 ensure doctor logged in via session


    if "user_id" not in session or session.get("role") != "doctor":


        return jsonify({"error": "Unauthorized - Doctor access required"}), 401


    # 🔗 get doctor from logged-in user


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first()


    if not doctor:


        # Auto-create doctor profile if missing


        user = User.query.get(session["user_id"])


        if user and user.role == "doctor":


            doctor = Doctor(


                user_id=user.id,


                name=user.username,


                email=user.email


            )


            db.session.add(doctor)


            db.session.commit()


        else:


            return jsonify({"error": "Doctor profile not found"}), 404


    # ✅ Auto-reject expired appointments first


    auto_reject_expired_appointments()


    # 🔥 fetch ONLY this doctor's appointments


    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.created_at.desc()).all()


    data = []


    for a in appointments:


        data.append({


            "id": a.id,


            "email": a.email,


            "date": a.date.isoformat(),


            "time": a.time.strftime("%H:%M") if a.time else "N/A",


            "issue": a.issue,


            "status": a.status,


            "completed_at": a.completed_at.isoformat() if a.completed_at else None,


            "reject_reason": a.reject_reason


        })


    return jsonify(data), 200


@app.route("/api/appointment/queue/<int:appointment_id>")


def appointment_queue(appointment_id):


    appointment = Appointment.query.get_or_404(appointment_id)


    pending = Appointment.query.filter(


        Appointment.doctor_id == appointment.doctor_id,


        Appointment.date == appointment.date,


        Appointment.status == "Pending"


    ).order_by(


        Appointment.time


    ).all()


    for index, appt in enumerate(pending):


        if appt.id == appointment_id:


            return {


                "patients_before": index,


                "your_position": index + 1


            }


    return {


        "patients_before": 0,


        "your_position": 0


    }


@app.route("/patient/appointment-queue")


def patient_queue_view():


    if session.get("role") != "patient":


        flash("Unauthorized", "danger")


        return redirect(url_for("login_view"))


    # Debug: Print session info


    print(f"DEBUG: Session keys: {list(session.keys())}")


    print(f"DEBUG: Session email: {session.get('email')}")


    print(f"DEBUG: Session role: {session.get('role')}")


    print(f"DEBUG: Session user_id: {session.get('user_id')}")


    # Get patient user


    patient_user = User.query.filter_by(email=session.get("email")).first()


    print(f"DEBUG: Found patient user: {patient_user}")


    if not patient_user:


        flash("User session invalid", "danger")


        return redirect(url_for("login_view"))


    # Fetch ALL patient's appointments (all statuses) using patient_id


    appointments = Appointment.query.filter_by(patient_id=patient_user.id).order_by(


        Appointment.date,


        Appointment.time


    ).all()


    print(f"DEBUG: Found {len(appointments)} appointments for patient {patient_user.id}")


    appointments_data = []


    for a in appointments:


        doctor = Doctor.query.get(a.doctor_id)


        appointments_data.append({


            "id": a.id,


            "patient_name": a.patient_name,


            "doctor_name": doctor.name if doctor else "Unknown",


            "date": a.date.strftime("%Y-%m-%d"),


            "time": a.time.strftime("%H:%M") if a.time else "N/A",


            "status": a.status,


            "completed_at": a.completed_at.strftime("%Y-%m-%d %H:%M") if a.completed_at else None,


            "reject_reason": a.reject_reason


        })


    print(f"DEBUG: Returning {len(appointments_data)} appointments to template")


    return render_template(


        "patient_appointment_queue.html",


        appointments=appointments_data


    )


# ------------------ Doctor: View Own Availability ------------------


@app.route("/doctor/availability")


def doctor_availability_page():


    if "user_id" not in session or session.get("role") != "doctor":


        return redirect(url_for("login_view"))


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first_or_404()


    availability = DoctorAvailability.query.filter_by(


        doctor_id=doctor.id


    ).all()


    return render_template(


        "doctor_availability.html",


        availability=availability,


        doctor=doctor,


        today_date=date.today().strftime('%Y-%m-%d')


    )


# ------------------ Doctor: Add Availability ------------------


@app.route("/doctor/add-availability", methods=["POST"])


def add_availability():


    if "user_id" not in session or session.get("role") != "doctor":


        abort(403)


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first_or_404()


    # Get date from form


    date_str = request.form["date"]


    try:


        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()


    except ValueError:


        flash("Invalid date format", "danger")


        return redirect(url_for("doctor_availability_page"))


    # Get times from form


    start_time_str = request.form["start_time"]


    end_time_str = request.form["end_time"]


    # Convert time strings to time objects


    start_time = datetime.strptime(start_time_str, '%H:%M').time()


    end_time = datetime.strptime(end_time_str, '%H:%M').time()


    # Validate time logic


    if start_time >= end_time:


        flash("Start time must be before end time", "danger")


        return redirect(url_for("doctor_availability_page"))


    slot = DoctorAvailability(


        doctor_id=doctor.id,


        date=selected_date,


        start_time=start_time,


        end_time=end_time,


        is_booked=False


    )


    db.session.add(slot)


    db.session.commit()


    flash("Availability added successfully ✅", "success")


    return redirect(url_for("doctor_availability_page"))


# ------------------ Doctor: Update Availability ------------------


@app.route("/doctor/update-availability/<int:slot_id>", methods=["POST"])


def update_availability(slot_id):


    if "user_id" not in session or session.get("role") != "doctor":


        abort(403)


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first_or_404()


    slot = DoctorAvailability.query.get_or_404(slot_id)


    # 🔐 Security: doctor can update only own slot


    if slot.doctor_id != doctor.id:


        abort(403)


    # Get times from form


    start_time_str = request.form["start_time"]


    end_time_str = request.form["end_time"]


    # Convert time strings to time objects


    start_time = datetime.strptime(start_time_str, '%H:%M').time()


    end_time = datetime.strptime(end_time_str, '%H:%M').time()


    # Validate time logic


    if start_time >= end_time:


        flash("Start time must be before end time", "danger")


        return redirect(url_for("doctor_availability_page"))


    slot.start_time = start_time


    slot.end_time = end_time


    db.session.commit()


    flash("Availability updated successfully ✅", "success")


    return redirect(url_for("doctor_availability_page"))


# ------------------ Doctor: Delete Availability ------------------


@app.route("/doctor/delete-availability/<int:slot_id>", methods=["POST"])


def delete_availability(slot_id):


    if "user_id" not in session or session.get("role") != "doctor":


        abort(403)


    doctor = Doctor.query.filter_by(user_id=session["user_id"]).first_or_404()


    slot = DoctorAvailability.query.get_or_404(slot_id)


    if slot.doctor_id != doctor.id:


        abort(403)


    if slot.is_booked:


        flash("Booked slot cannot be deleted", "warning")


        return redirect(url_for("doctor_availability_page"))


    db.session.delete(slot)


    db.session.commit()


    flash("Availability deleted successfully ✅", "success")


    return redirect(url_for("doctor_availability_page"))


# ------------------ Patient: View Doctor Availability API ------------------


@app.route("/api/patient/doctor-availability/<int:doctor_id>")


def api_doctor_availability(doctor_id):


    """API to get doctor availability for specific date"""


    # Get date from query parameter


    date_str = request.args.get('date')


    if not date_str:


        return jsonify({"error": "Date parameter required"}), 400


    try:


        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()


    except ValueError:


        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400


    # Verify doctor exists using user_id (since frontend sends user_id)


    doctor_user = User.query.filter_by(id=doctor_id, role="doctor").first()


    if not doctor_user:


        print(f"DEBUG: Doctor user not found with user_id {doctor_id}")


        return jsonify({"error": "Doctor not found"}), 404


    doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()


    if not doctor:


        print(f"DEBUG: Doctor profile not found for user {doctor_id}")


        return jsonify({"error": "Doctor profile not found"}), 404


    print(f"DEBUG: Found doctor: {doctor.name} (ID: {doctor.id})")


    # Query availability for specific doctor and date


    availability = DoctorAvailability.query.filter(


        DoctorAvailability.doctor_id == doctor.id,  # Use doctor.id, not user_id


        DoctorAvailability.date == selected_date,


        DoctorAvailability.is_booked == False


    ).order_by(DoctorAvailability.start_time).all()


    print(f"DEBUG: Found {len(availability)} raw availability slots")


    # Return available time slots in 12-hour format

    slots = []

    for slot in availability:

        # Only include future times on the same date, or any time on future dates

        if (slot.date > date.today()) or \
           (slot.date == date.today() and slot.start_time >= datetime.now().time()):
            slots.append({

                "id": slot.id,

                "date": slot.date.isoformat(),

                "start_time": slot.start_time.strftime("%I:%M %p"),

                "end_time": slot.end_time.strftime("%I:%M %p"),

                "is_booked": slot.is_booked

            })

    # Debug logging

    print(f"DEBUG: Doctor {doctor_id} availability for {date_str}: {len(slots)} slots found")

    for slot in slots:

        print(f"DEBUG: Slot {slot['id']}: {slot['start_time']} - {slot['end_time']}")

    return jsonify({

        "doctor_id": doctor_id,


        "doctor_name": doctor.name,


        "date": date_str,


        "available_slots": slots


    })


#from routes import *;


# ------------------ Patient: View Doctor Availability Page ------------------


@app.route("/patient/doctor-availability/<int:user_id>")


def patient_doctor_availability_page(user_id):


    # Doctor user


    doctor_user = User.query.filter_by(id=user_id, role="doctor").first_or_404()


    # Doctor profile


    doctor = Doctor.query.filter_by(user_id=user_id).first_or_404()


    today = date.today()  # Use current date


    # Get ALL slots (both available and booked) so patients can see complete schedule


    availability = DoctorAvailability.query.filter(


        DoctorAvailability.doctor_id == doctor.id,


        DoctorAvailability.date >= today


    ).order_by(


        DoctorAvailability.date,


        DoctorAvailability.start_time


    ).all()


    return render_template(


        "patient_doctor_availability.html",


        doctor=doctor,


        doctor_user=doctor_user,


        availability=availability


    )


print("ROUTE HIT SUCCESSFULLY")


@app.route("/contact")


def contact_page():


    # Get all doctors for the availability button


    doctors = User.query.filter_by(role="doctor").all()


    return render_template("contact.html", doctors=doctors)


# ------------------ Patients API ------------------


@app.route("/api/patients", methods=["GET"])


def get_patients():


    """Get list of all registered patients (session-based auth for doctors)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") != "doctor":


            return jsonify({"error": "Unauthorized - Doctor access required"}), 401


        # Get all registered patients


        patients = User.query.filter_by(role='patient').all()


        patient_list = []


        for patient_user in patients:


            patient_list.append({


                "_id": patient_user.id,


                "name": patient_user.username


            })


        return jsonify({


            "success": True,


            "patients": patient_list


        })


    except Exception as e:


        print(f"Error getting patients: {e}")


        return jsonify({"error": "Failed to load patients"}), 500


# ------------------ Doctors API ------------------


@app.route("/api/doctors", methods=["GET"])


def get_doctors():


    """Get list of all registered doctors (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") != "patient":


            return jsonify({"error": "Unauthorized - Patient access required"}), 401


        # Get ALL registered doctors (not just approved ones)


        doctors = User.query.filter_by(role='doctor').all()


        doctor_list = []


        for doctor_user in doctors:


            # Get doctor profile for additional info


            doctor_profile = Doctor.query.filter_by(user_id=doctor_user.id).first()


            doctor_list.append({


                "_id": doctor_user.id,


                "name": doctor_profile.name if doctor_profile else doctor_user.username,


                "specialization": doctor_profile.specialization if doctor_profile else "General"


            })


        return jsonify({


            "success": True,


            "doctors": doctor_list


        })


    except Exception as e:


        print(f"Error getting doctors: {e}")


        return jsonify({"error": "Failed to load doctors"}), 500


# ------------------ Public Doctor List API (No Auth Required) ------------------


@app.route("/api/public/doctors", methods=["GET"])


def get_public_doctors():


    """Get list of approved doctors without authentication


    Endpoint: GET /api/public/doctors


    Response format:


    {


        "success": true,


        "doctors": [


            { "id": <int>, "username": <string>, "name": <string> }


        ]


    }


    """


    try:


        # Get all doctors with their profiles


        doctors = User.query.filter_by(role='doctor').all()


        doctor_list = []


        for doctor_user in doctors:


            # Get doctor profile for additional info


            doctor_profile = Doctor.query.filter_by(user_id=doctor_user.id).first()


            doctor_list.append({


                "id": doctor_user.id,


                "username": doctor_user.username,


                "name": doctor_profile.name if doctor_profile else doctor_user.username,


                "specialization": doctor_profile.specialization if doctor_profile else "General"


            })


        return jsonify({


            "success": True,


            "doctors": doctor_list


        })


    except Exception as e:


        print(f"Error getting public doctors: {e}")


        return jsonify({"error": "Failed to load doctors"}), 500


# ------------------ User List API ------------------


@app.route("/api/users", methods=["GET"])


@token_required


def get_users_by_role():


    """Get users by role (doctor or patient) with JWT authentication


    Endpoint:


    GET /api/users?role=doctor


    GET /api/users?role=patient


    Response format:


    {


        "success": true,


        "users": [


            { "id": <int>, "username": <string> }


        ]


    }


    """


    try:


        # Check session authentication\n        if " user_id\ not in session or session.get(\role\) not in [\doctor\, \patient\]:\n return jsonify({\error\: \Unauthorized\}), 401\n \n current_user_id = session[\user_id\]


        current_role = request.current_role


        # Get role from query parameter


        requested_role = request.args.get('role')


        if not requested_role or requested_role not in ['doctor', 'patient']:


            return jsonify({"error": "Invalid role parameter"}), 400


        # Only allow patients to get doctors and doctors to get patients


        if current_role == 'patient' and requested_role != 'doctor':


            return jsonify({"error": "Patients can only view doctors"}), 403


        if current_role == 'doctor' and requested_role != 'patient':


            return jsonify({"error": "Doctors can only view patients"}), 403


        # Query PostgreSQL users table using role column


        users = User.query.filter_by(role=requested_role).all()


        # Format response exactly as frontend expects


        user_list = []


        for user in users:


            user_list.append({


                "id": user.id,


                "username": user.username


            })


        return jsonify({


            "success": True,


            "users": user_list


        })


    except Exception as e:


        print(f"ERROR in get_users_by_role: {str(e)}")


        return jsonify({"error": "Failed to fetch users"}), 500


# ------------------ Send Message API (for doctor chat) ------------------


@app.route("/api/messages", methods=["POST"])


def send_message_api():


    """Send message from doctor to patient or patient to doctor (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:


            return jsonify({"error": "Unauthorized access required"}), 401


        current_user_id = session["user_id"]


        current_role = session.get("role")


        data = request.get_json()


        if not data or "receiverId" not in data or "message" not in data:


            return jsonify({"error": "Missing receiverId or message"}), 400


        receiver_id = int(data["receiverId"])


        message_text = data["message"].strip()


        # Prevent users from messaging themselves


        if current_user_id == receiver_id:


            return jsonify({"error": "Cannot message yourself"}), 400


        if not message_text:


            return jsonify({"error": "Message cannot be empty"}), 400


        # Verify receiver exists and has opposite role


        receiver_user = User.query.get(receiver_id)


        if not receiver_user:


            return jsonify({"error": "Invalid receiver"}), 400


        # Ensure doctor-patient communication only


        if current_role == 'patient' and receiver_user.role != 'doctor':


            return jsonify({"error": "Patients can only message doctors"}), 400


        if current_role == 'doctor' and receiver_user.role != 'patient':


            return jsonify({"error": "Doctors can only message patients"}), 400


        # Create message


        message = Message(


            sender_id=current_user_id,


            receiver_id=receiver_id,


            sender_role=current_role,


            receiver_role=receiver_user.role,


            message=message_text


        )


        db.session.add(message)


        db.session.commit()


        return jsonify({


            "success": True,


            "message": "Message sent successfully"


        })


    except Exception as e:


        print(f"ERROR in send_message_api: {str(e)}")


        db.session.rollback()


        return jsonify({"error": "Failed to send message"}), 500


# ------------------ Get Messages API (for patient and doctor chat) ------------------


@app.route("/api/messages/<int:other_user_id>", methods=["GET"])


def get_messages_with_user(other_user_id):


    """Get conversation between logged-in user and specific user (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:


            return jsonify({"error": "Unauthorized access required"}), 401


        current_user_id = session["user_id"]


        current_role = session.get("role")


        # Prevent users from chatting with themselves


        if current_user_id == other_user_id:


            return jsonify({"error": "Cannot chat with yourself"}), 400


        # Verify other user exists


        other_user = User.query.get(other_user_id)


        if not other_user:


            return jsonify({"error": "Invalid user"}), 400


        # Ensure doctor-patient communication only


        if current_role == 'patient' and other_user.role != 'doctor':


            return jsonify({"error": "Patients can only chat with doctors"}), 400


        if current_role == 'doctor' and other_user.role != 'patient':


            return jsonify({"error": "Doctors can only chat with patients"}), 400


        # Get messages between users


        messages = Message.query.filter(


            ((Message.sender_id == current_user_id) & (Message.receiver_id == other_user_id)) |


            ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user_id))


        ).filter(


            Message.is_deleted_by_sender == False,


            Message.is_deleted_by_receiver == False


        ).order_by(Message.created_at.asc()).all()


        message_list = []


        for msg in messages:


            message_list.append({


                "id": msg.id,


                "message": msg.message,


                "createdAt": msg.created_at.isoformat(),


                "isFromCurrentUser": msg.sender_id == current_user_id,


                "senderId": msg.sender_id,


                "receiverId": msg.receiver_id


            })


        return jsonify({


            "success": True,


            "messages": message_list


        })


    except Exception as e:


        print(f"ERROR in get_messages_with_user: {str(e)}")


        return jsonify({"error": "Failed to load messages"}), 500


# ------------------ Send Message API ------------------


@app.route("/api/chat/send", methods=["POST"])


def send_chat_message():


    """Send chat message with session authentication

    Endpoint: POST /api/chat/send

    Body: { "message": <string>, "receiverId": <int>, "senderRole": <string> }

    Sender ID comes from session

    Message saved to PostgreSQL

    """


    try:
        # Check session authentication
        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:
            return jsonify({"error": "Unauthorized"}), 401

        current_user_id = session["user_id"]
        current_role = session.get("role")

        # Get request data


        data = request.get_json()


        if not data:


            return jsonify({"error": "No data provided"}), 400


        message_text = data.get("message", "").strip()


        receiver_id = data.get("receiverId")


        sender_role = data.get("senderRole", current_role)  # Use session role as default


        # Validate inputs


        if not message_text:


            return jsonify({"error": "Message cannot be empty"}), 400


        # Prevent users from messaging themselves


        if current_user_id == receiver_id:


            return jsonify({"error": "Cannot message yourself"}), 400


        if not receiver_id or not isinstance(receiver_id, int) or receiver_id <= 0:


            return jsonify({"error": "Invalid receiver ID"}), 400


        # Get receiver info from PostgreSQL


        receiver = User.query.get(receiver_id)


        if not receiver:


            return jsonify({"error": "Receiver not found"}), 400


        # Validate sender role matches session role


        if sender_role != current_role:


            return jsonify({"error": "Sender role mismatch"}), 403


        # Ensure different roles (patient ↔ doctor)


        if current_role == receiver.role:


            return jsonify({"error": "You can only message users with different roles"}), 400


        # Create message in PostgreSQL


        message = Message(


            sender_id=current_user_id,


            receiver_id=receiver_id,


            sender_role=sender_role,


            receiver_role=receiver.role,


            message=message_text


        )


        db.session.add(message)


        db.session.commit()


        return jsonify({


            "success": True,


            "message": {


                "id": message.id,


                "senderId": message.sender_id,


                "receiverId": message.receiver_id,


                "senderRole": message.sender_role,


                "receiverRole": message.receiver_role,


                "message": message.message,


                "createdAt": message.created_at.isoformat()


            }


        })


    except Exception as e:


        print(f"ERROR in send_chat_message: {str(e)}")


        db.session.rollback()


        return jsonify({"error": "Failed to send message"}), 500


# ------------------ Load Chat History API ------------------


@app.route("/api/chat/history/<int:receiverId>", methods=["GET"])


def get_chat_history_with_receiver(receiverId):


    try:


        # Check session authentication\n        if " user_id\ not in session or session.get(\role\) not in [\doctor\, \patient\]:\n return jsonify({\error\: \Unauthorized\}), 401\n \n current_user_id = session[\user_id\]


        current_role = request.current_role


        # Prevent users from chatting with themselves


        if current_user_id == receiverId:


            return jsonify({"error": "Cannot chat with yourself"}), 400


        # Validate receiverId


        if not isinstance(receiverId, int) or receiverId <= 0:


            return jsonify({"error": "Invalid receiver ID"}), 400


        # Get receiver info from PostgreSQL


        receiver = User.query.get(receiverId)


        if not receiver:


            return jsonify({"error": "Receiver not found"}), 404


        # Query PostgreSQL for messages between users


        messages = Message.query.filter(


            db.or_(


                db.and_(


                    Message.sender_id == current_user_id,


                    Message.receiver_id == receiverId,


                    Message.is_deleted_by_sender == False


                ),


                db.and_(


                    Message.sender_id == receiverId,


                    Message.receiver_id == current_user_id,


                    Message.is_deleted_by_receiver == False


                )


            )


        ).order_by(Message.created_at.asc()).all()


        # Format response exactly as frontend expects


        chat_history = []


        for msg in messages:


            chat_history.append({


                "message": msg.message,


                "createdAt": msg.created_at.isoformat(),


                "isFromCurrentUser": msg.sender_id == current_user_id


            })


        return jsonify({


            "success": True,


            "messages": chat_history


        })


    except Exception as e:


        print(f"ERROR in get_chat_history_with_receiver: {str(e)}")


        return jsonify({"error": "Failed to load chat history"}), 500


# ------------------ Delete Chat API ------------------


@app.route("/api/messages/conversation/<int:receiverId>", methods=["DELETE"])


def delete_conversation(receiverId):


    """Delete conversation between logged-in user and specific receiver (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:


            return jsonify({"error": "Unauthorized access required"}), 401


        current_user_id = session["user_id"]


        current_role = session.get("role")


        # Validate receiverId


        if not isinstance(receiverId, int) or receiverId <= 0:


            return jsonify({"error": "Invalid receiver ID"}), 400


        # Verify receiver exists and has opposite role


        receiver_user = User.query.get(receiverId)


        if not receiver_user:


            return jsonify({"error": "Receiver not found"}), 404


        # Ensure doctor-patient communication only


        if current_role == 'patient' and receiver_user.role != 'doctor':


            return jsonify({"error": "Patients can only delete conversations with doctors"}), 400


        if current_role == 'doctor' and receiver_user.role != 'patient':


            return jsonify({"error": "Doctors can only delete conversations with patients"}), 400


        # Soft delete all messages in this conversation for the current user


        messages_to_delete = Message.query.filter(


            ((Message.sender_id == current_user_id) & (Message.receiver_id == receiverId)) |


            ((Message.sender_id == receiverId) & (Message.receiver_id == current_user_id))


        ).all()


        for message in messages_to_delete:


            if message.sender_id == current_user_id:


                message.is_deleted_by_sender = True


            if message.receiver_id == current_user_id:


                message.is_deleted_by_receiver = True


        db.session.commit()


        return jsonify({


            "success": True,


            "message": "Conversation deleted successfully"


        })


    except Exception as e:


        print(f"ERROR in delete_conversation: {str(e)}")


        db.session.rollback()


        return jsonify({"error": "Failed to delete conversation"}), 500


@app.route("/api/messages/history", methods=["GET"])


@token_required


def get_chat_history():


    """Get chat history for logged-in user"""


    try:


        # Check session authentication\n        if " user_id\ not in session or session.get(\role\) not in [\doctor\, \patient\]:\n return jsonify({\error\: \Unauthorized\}), 401\n \n current_user_id = session[\user_id\]


        current_role = request.current_role


        # Get messages where user is either sender or receiver


        # Apply soft delete filters


        messages = Message.query.filter(


            db.or_(


                db.and_(


                    Message.sender_id == current_user_id,


                    Message.is_deleted_by_sender == False


                ),


                db.and_(


                    Message.receiver_id == current_user_id,


                    Message.is_deleted_by_receiver == False


                )


            )


        ).order_by(Message.created_at.asc()).all()


        chat_history = []


        for msg in messages:


            chat_history.append({


                "id": msg.id,


                "senderId": msg.sender_id,


                "receiverId": msg.receiver_id,


                "senderRole": msg.sender_role,


                "receiverRole": msg.receiver_role,


                "message": msg.message,


                "createdAt": msg.created_at.isoformat(),


                "isDeletedBySender": msg.is_deleted_by_sender,


                "isDeletedByReceiver": msg.is_deleted_by_receiver,


                "isFromCurrentUser": msg.sender_id == current_user_id


            })


        return jsonify({


            "success": True,


            "messages": chat_history


        })


    except Exception as e:


        print(f"ERROR in get_chat_history: {str(e)}")


        return jsonify({"error": "Failed to load chat history"}), 500


@app.route("/api/messages/<int:message_id>/delete", methods=["DELETE"])


def delete_message(message_id):


    """Soft delete a message for the logged-in user only (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:


            return jsonify({"error": "Unauthorized access required"}), 401


        current_user_id = session["user_id"]


        # Get the message


        message = Message.query.get(message_id)


        if not message:


            return jsonify({"error": "Message not found"}), 404


        # Check if user is sender or receiver


        if message.sender_id != current_user_id and message.receiver_id != current_user_id:


            return jsonify({"error": "You can only delete your own messages"}), 403


        # Soft delete for sender


        if message.sender_id == current_user_id:


            message.is_deleted_by_sender = True


        # Soft delete for receiver


        if message.receiver_id == current_user_id:


            message.is_deleted_by_receiver = True


        db.session.commit()


        return jsonify({


            "success": True,


            "message": "Message deleted successfully"


        })


    except Exception as e:


        print(f"ERROR in delete_message: {str(e)}")


        db.session.rollback()


        return jsonify({"error": "Failed to delete message"}), 500


@app.route("/api/messages/conversation/<int:other_user_id>", methods=["GET"])


def get_conversation_with_user(other_user_id):


    """Get conversation between logged-in user and specific user (session-based auth)"""


    try:


        # Check session authentication


        if "user_id" not in session or session.get("role") not in ["doctor", "patient"]:


            return jsonify({"error": "Unauthorized access required"}), 401


        current_user_id = session["user_id"]


        current_role = session.get("role")


        # Prevent users from chatting with themselves


        if current_user_id == other_user_id:


            return jsonify({"error": "Cannot chat with yourself"}), 400


        # Validate other_user_id


        if not isinstance(other_user_id, int) or other_user_id <= 0:


            return jsonify({"error": "Invalid user ID"}), 400


        # Verify other user exists and has opposite role


        other_user = User.query.get(other_user_id)


        if not other_user:


            return jsonify({"error": "User not found"}), 404


        # Ensure doctor-patient communication only


        if current_role == 'patient' and other_user.role != 'doctor':


            return jsonify({"error": "Patients can only chat with doctors"}), 400


        if current_role == 'doctor' and other_user.role != 'patient':


            return jsonify({"error": "Doctors can only chat with patients"}), 400


        # Get messages between these two users


        # Apply soft delete filters


        messages = Message.query.filter(


            db.and_(


                db.or_(


                    db.and_(


                        Message.sender_id == current_user_id,


                        Message.receiver_id == other_user_id,


                        Message.is_deleted_by_sender == False


                    ),


                    db.and_(


                        Message.sender_id == other_user_id,


                        Message.receiver_id == current_user_id,


                        Message.is_deleted_by_receiver == False


                    )


                )


            )


        ).order_by(Message.created_at.asc()).all()


        conversation = []


        for msg in messages:


            conversation.append({


                "id": msg.id,


                "senderId": msg.sender_id,


                "receiverId": msg.receiver_id,


                "senderRole": msg.sender_role,


                "receiverRole": msg.receiver_role,


                "message": msg.message,


                "createdAt": msg.created_at.isoformat(),


                "isDeletedBySender": msg.is_deleted_by_sender,


                "isDeletedByReceiver": msg.is_deleted_by_receiver,


                "isFromCurrentUser": msg.sender_id == current_user_id


            })


        return jsonify({


            "success": True,


            "conversation": conversation


        })


    except Exception as e:


        print(f"ERROR in get_conversation_with_user: {str(e)}")


        return jsonify({"error": "Failed to load conversation"}), 500


@app.route("/api/messages/contacts", methods=["GET"])


@token_required


def get_messaging_contacts():


    """Get list of users the current user can message (all registered users by role)"""


    try:


        # Check session authentication\n        if " user_id\ not in session or session.get(\role\) not in [\doctor\, \patient\]:\n return jsonify({\error\: \Unauthorized\}), 401\n \n current_user_id = session[\user_id\]


        current_role = request.current_role


        contacts = []


        if current_role == "patient":


            # Patient can message ALL registered doctors


            doctors = User.query.filter_by(role='doctor').all()


            for doctor in doctors:


                contacts.append({


                    "id": doctor.id,


                    "name": doctor.username,


                    "role": doctor.role


                })


        elif current_role == "doctor":


            # Doctor can message ALL registered patients


            patients = User.query.filter_by(role='patient').all()


            for patient in patients:


                contacts.append({


                    "id": patient.id,


                    "name": patient.username,


                    "role": patient.role


                })


        return jsonify({


            "success": True,


            "contacts": contacts


        })


    except Exception as e:


        print(f"ERROR in get_messaging_contacts: {str(e)}")


        return jsonify({"error": "Failed to load contacts"}), 500


# Simple test route to verify basic routing works


@app.route("/test-simple")


def test_simple():


    return "Simple test route is working!"


@app.route("/forgot-password", methods=["POST"])


def forgot_password():


    email = request.form.get("email")


    user = User.query.filter_by(email=email).first()


    if not user:


        flash("Email not registered ❌", "danger")


        return redirect(url_for("login_view"))


    token = serializer.dumps(email, salt="reset-password")


    reset_link = url_for("reset_password", token=token, _external=True)


    # 🔥 TESTING PURPOSE (terminal मध्ये link दिसेल)


    print("RESET PASSWORD LINK:", reset_link)


    flash("Password reset link sent (check terminal) ✅", "success")


    return redirect(url_for("login_view"))


@app.route("/reset-password/<token>", methods=["GET","POST"])


def reset_password(token):


    try:


        email = serializer.loads(token, salt="reset-password", max_age=1800)


    except:


        flash("Reset link expired ❌", "danger")


        return redirect(url_for("login_view"))


    if request.method == "POST":


        password = request.form.get("password")


        confirm = request.form.get("confirm_password")


        if password != confirm:


            flash("Passwords do not match ❌", "danger")


            return redirect(request.url)


        user = User.query.filter_by(email=email).first()


        user.password = generate_password_hash(password)


        db.session.commit()


        flash("Password reset successful ✅", "success")


        return redirect(url_for("login_view"))


    return render_template("reset_password.html")


@socketio.on("disconnect")


def on_disconnect():


    print("SERVER: client disconnected:", request.sid)


@socketio.on("join")


def handle_join(data):


    print("ROOM JOIN:", data["room"])


    join_room(data["room"])


@socketio.on("message")


def handle_message(data):


    room = data["room"]


    sender = data["sender"]


    msg = data["message"]


    entry = {


        "sender": sender,


        "message": msg,


        "timestamp": str(datetime.now())


    }


    chat_history.setdefault(room, []).append(entry)


    emit("new_message", entry, room=room)


if __name__ == "__main__":


    with app.app_context():


        db.create_all()


    socketio.run(app, host="127.0.0.1", port=5000, debug=True)


# ---------------------- Run App ----------------------


#if __name__ == "__main__":


 #   app.run(debug=True, port=5000)