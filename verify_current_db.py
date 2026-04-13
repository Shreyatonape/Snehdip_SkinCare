import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

print('=== Current Database Schema ===')

# Check users table
inspector = db.inspect(db.engine)
if 'users' in inspector.get_table_names():
    columns = inspector.get_columns('users')
    print('users table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')

    # Verify required columns exist
    required_columns = ['id', 'username', 'email', 'password', 'role', 'created_at']
    existing_columns = [col['name'] for col in columns]

    print('\n=== Column Verification ===')
    for col in required_columns:
        if col in existing_columns:
            print(f'✅ {col} - EXISTS')
        else:
            print(f'❌ {col} - MISSING')

    # Check for problematic columns
    problematic_columns = ['name', 'is_online', 'last_seen']
    print('\n=== Problematic Columns Check ===')
    for col in problematic_columns:
        if col in existing_columns:
            print(f'❌ {col} - EXISTS (should not exist)')
        else:
            print(f'✅ {col} - NOT EXISTS (good)')
else:
    print('❌ users table does not exist')

# Check if chat_messages table exists
if 'chat_messages' in inspector.get_table_names():
    columns = inspector.get_columns('chat_messages')
    print('\nchat_messages table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')
else:
    print('\n❌ chat_messages table does not exist')

# Test User model
print('\n=== Test User Model ===')
try:
    from models import User
    users = User.query.limit(1).all()
    print('✅ User model works')
    if users:
        user = users[0]
        print(f'✅ Sample user: {user.username} ({user.role})')
except Exception as e:
    print(f'❌ User model error: {e}')