# Flask Skincare Project - Database Setup & Migration Guide

## 🚀 Quick Setup Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup (PostgreSQL)
Make sure PostgreSQL is running and database `skincare_db` exists:
```sql
CREATE DATABASE skincare_db;
CREATE USER postgres WITH PASSWORD 'pass@123';
GRANT ALL PRIVILEGES ON DATABASE skincare_db TO postgres;
```

### 3. Initialize Database
```bash
python migrate.py init
```

### 4. Run Application
```bash
python app.py
```

## 📋 Migration Commands

### For Development:
```bash
# Reset entire database (WARNING: Deletes all data)
python migrate.py reset

# Initialize with fresh tables
python migrate.py init
```

### For Production:
```bash
# Create new migration
python migrate.py create

# Apply migrations
python migrate.py upgrade
```

## 🛠️ Manual Database Operations

### Check Current Schema:
```bash
python check_postgres_db.py
```

### Fix Schema Issues:
If you encounter column errors, run:
```bash
python fix_database_schema.py
```

## 🔧 Environment Variables

Create `.env` file:
```
SECRET_KEY=a1b2c3d4e5f6g7h8
DATABASE_URL=postgresql://postgres:pass%40123@localhost:5432/skincare_db
GEMINI_API_KEY=your_api_key_here
```

## 📊 Model Changes Made

### Fixed Issues:
1. ✅ Removed `is_approved` and `is_admin` columns from User model
2. ✅ Made `doctor_id` nullable in Appointment model
3. ✅ Added proper `__repr__` methods to all models
4. ✅ Cleaned up duplicate imports
5. ✅ Fixed TensorFlow warnings and model loading

### Current Models:
- **User**: id, username, email, password, role, created_at
- **Doctor**: id, user_id, name, email, specialization, profile_image
- **Appointment**: id, patient_id, patient_name, email, doctor_id, date, time, issue, status, reject_reason, created_at, completed_at
- **MedicalRecord**: id, patient_id, doctor_id, diagnosis, confidence, risk_level, reason, symptoms, prevention, image_path, created_at
- **DoctorAvailability**: id, doctor_id, date, start_time, end_time, is_booked
- **Message**: id, sender_id, receiver_id, sender_role, receiver_role, message, created_at, is_deleted_by_sender, is_deleted_by_receiver

## 🐛 Common Issues & Solutions

### 1. "column users.is_approved does not exist"
**Solution**: The models have been updated to remove these columns. Run:
```bash
python migrate.py reset
python migrate.py init
```

### 2. TensorFlow Warnings
**Solution**: These are now suppressed. The model loads with `compile=False` to avoid optimizer warnings.

### 3. Migration Conflicts
**Solution**: Delete the `migrations/versions` folder and recreate:
```bash
rm -rf migrations/versions
python migrate.py create
python migrate.py upgrade
```

## 🔄 Database Reset Workflow

For a clean start:
```bash
# 1. Stop the application if running
# 2. Reset database
python migrate.py reset

# 3. Initialize fresh schema
python migrate.py init

# 4. (Optional) Create admin user manually
python -c "
from app import create_app
from models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        role='doctor'
    )
    from extensions import db
    db.session.add(admin)
    db.session.commit()
    print('Admin user created')
"

# 5. Start application
python app.py
```

## 📝 Notes

- The project now uses PostgreSQL exclusively
- SQLite references have been removed
- All admin approval logic has been simplified to role-based access
- TensorFlow model loading is now error-handled
- Database schema matches the models exactly

## 🚨 Important

- Always backup your database before running reset operations
- Use `python migrate.py reset` only in development
- In production, use proper migration scripts with `python migrate.py upgrade`
