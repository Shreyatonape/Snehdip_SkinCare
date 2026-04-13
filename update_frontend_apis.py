"""
Script to update frontend JavaScript to use new messaging APIs
"""

import os
import re

def update_patient_chat():
    """Update patient_chat.html to use new APIs"""
    file_path = "templates/patient_chat.html"

    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Update API endpoints
    content = content.replace(
        'fetch(\'/api/doctors\'',
        'fetch(\'/api/messages/contacts\')'
    )

    content = content.replace(
        'fetch(`/api/chat/conversation/${doctorId}`',
        'fetch(`/api/messages/conversation/${doctorId}`'
    )

    content = content.replace(
        'fetch(\'/api/chat/send\'',
        'fetch(\'/api/messages/send\')'
    )

    content = content.replace(
        'fetch(`/api/chat/conversation/${selectedDoctorId}`',
        'fetch(`/api/messages/conversation/${selectedDoctorId}`'
    )

    # Update response handling
    content = content.replace(
        'data.doctors',
        'data.contacts'
    )

    content = content.replace(
        'data.conversation',
        'data.conversation'
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated patient_chat.html with new messaging APIs")

def update_doctor_chat():
    """Update doctor_chat.html to use new APIs"""
    file_path = "templates/doctor_chat.html"

    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Update API endpoints
    content = content.replace(
        'fetch(\'/api/patients\'',
        'fetch(\'/api/messages/contacts\')'
    )

    content = content.replace(
        'fetch(`/api/chat/conversation/${patientId}`',
        'fetch(`/api/messages/conversation/${patientId}`'
    )

    content = content.replace(
        'fetch(\'/api/chat/send\'',
        'fetch(\'/api/messages/send\')'
    )

    # Update response handling
    content = content.replace(
        'data.patients',
        'data.contacts'
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated doctor_chat.html with new messaging APIs")

if __name__ == "__main__":
    print("=== Updating Frontend APIs ===")
    update_patient_chat()
    update_doctor_chat()
    print("\n✅ Frontend updated to use new role-based messaging APIs")
    print("\nNew API Endpoints:")
    print("- GET  /api/messages/contacts - Get list of users to message")
    print("- POST /api/messages/send - Send a message")
    print("- GET  /api/messages/conversation/<id> - Get conversation with user")
    print("- DELETE /api/messages/<id>/delete - Delete a message")
    print("- GET  /api/messages/history - Get all messages for user")