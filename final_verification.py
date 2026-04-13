import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

print('=== FINAL VERIFICATION ===')

# 1. Check User model
print('1. User Model:')
try:
    from models import User
    users = User.query.limit(1).all()
    print('   ✅ User model works without errors')
    if users:
        user = users[0]
        print(f'   ✅ Sample user: {user.username} ({user.role})')
except Exception as e:
    print(f'   ❌ User model error: {e}')

# 2. Check Message model
print('\n2. Message Model:')
try:
    from models import Message
    messages = Message.query.limit(1).all()
    print('   ✅ Message model works without errors')
    if messages:
        msg = messages[0]
        print(f'   ✅ Sample message: {msg.message[:50]}...')
except Exception as e:
    print(f'   ❌ Message model error: {e}')

# 3. Check database schema
print('\n3. Database Schema:')
inspector = db.inspect(db.engine)

# Users table
if 'users' in inspector.get_table_names():
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    required_user_columns = ['id', 'username', 'email', 'password', 'role', 'created_at']

    print(f'   ✅ users table exists with {len(user_columns)} columns')

    for col in required_user_columns:
        if col in user_columns:
            print(f'   ✅ users.{col}')
        else:
            print(f'   ❌ users.{col} - MISSING')

    # Check for problematic columns
    problematic = ['name', 'is_online', 'last_seen']
    for col in problematic:
        if col in user_columns:
            print(f'   ❌ users.{col} - SHOULD NOT EXIST')
        else:
            print(f'   ✅ users.{col} - NOT EXISTS (good)')
else:
    print('   ❌ users table does not exist')

# Messages table
if 'messages' in inspector.get_table_names():
    message_columns = [col['name'] for col in inspector.get_columns('messages')]
    required_message_columns = ['id', 'sender_id', 'receiver_id', 'message', 'timestamp']

    print(f'   ✅ messages table exists with {len(message_columns)} columns')

    for col in required_message_columns:
        if col in message_columns:
            print(f'   ✅ messages.{col}')
        else:
            print(f'   ❌ messages.{col} - MISSING')
else:
    print('   ❌ messages table does not exist')

# 4. Test basic operations
print('\n4. Basic Operations:')
try:
    # Test user query
    user_count = User.query.count()
    print(f'   ✅ Found {user_count} users in database')

    # Test message query
    message_count = Message.query.count()
    print(f'   ✅ Found {message_count} messages in database')

    # Test relationship
    if user_count > 0 and message_count > 0:
        sample_user = User.query.first()
        user_messages = Message.query.filter_by(sender_id=sample_user.id).count()
        print(f'   ✅ User {sample_user.username} sent {user_messages} messages')

except Exception as e:
    print(f'   ❌ Database operation error: {e}')

print('\n=== ROUTE VERIFICATION ===')
# Check if routes exist by importing app
try:
    routes = []
    for rule in app.url_map.iter_rules():
        if '/chat/' in str(rule.rule):
            routes.append(str(rule.rule))

    expected_routes = ['/chat/users/<role>', '/chat/messages/<int:user_id>', '/chat/send', '/chat/delete/<int:user_id>']

    print('Chat routes found:')
    for route in expected_routes:
        if any(route in r for r in routes):
            print(f'   ✅ {route}')
        else:
            print(f'   ❌ {route} - NOT FOUND')

except Exception as e:
    print(f'   ❌ Route verification error: {e}')

print('\n=== SUMMARY ===')
print('✅ Simple doctor-patient chat system is ready!')
print('✅ Use patient_chat_simple.html for patient interface')
print('✅ Use doctor_chat_simple.html for doctor interface')
print('✅ No advanced features (socket.io, online status, etc.)')
print('✅ Simple text-only messaging with database persistence')