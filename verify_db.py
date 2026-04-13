import sys
sys.path.append('.')
from app import app
from extensions import db
app.app_context().push()

# Verify database schema
inspector = db.inspect(db.engine)
print('=== Database Schema Verification ===')

if 'users' in inspector.get_table_names():
    columns = inspector.get_columns('users')
    print('users table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')

    # Check for problematic columns
    column_names = [col['name'] for col in columns]
    if 'is_online' in column_names:
        print('❌ ERROR: is_online column still exists')
    else:
        print('✅ is_online column removed')

    if 'last_seen' in column_names:
        print('❌ ERROR: last_seen column still exists')
    else:
        print('✅ last_seen column removed')
else:
    print('❌ ERROR: users table does not exist')

if 'chat_messages' in inspector.get_table_names():
    columns = inspector.get_columns('chat_messages')
    print('chat_messages table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')

    # Check for problematic columns
    column_names = [col['name'] for col in columns]
    if 'room_name' in column_names:
        print('❌ ERROR: room_name column still exists')
    else:
        print('✅ room_name column removed')

    if 'is_read' in column_names:
        print('❌ ERROR: is_read column still exists')
    else:
        print('✅ is_read column removed')
else:
    print('❌ ERROR: chat_messages table does not exist')

print('\n=== Test User Query ===')
try:
    from models import User
    users = User.query.limit(1).all()
    print('✅ User query works without errors')
    if users:
        user = users[0]
        print(f'✅ Sample user: {user.username} ({user.role})')
except Exception as e:
    print(f'❌ ERROR in User query: {e}')

print('\n=== Test ChatMessage Query ===')
try:
    from models import ChatMessage
    messages = ChatMessage.query.limit(1).all()
    print('✅ ChatMessage query works without errors')
    if messages:
        msg = messages[0]
        print(f'✅ Sample message: {msg.message[:50]}...')
except Exception as e:
    print(f'❌ ERROR in ChatMessage query: {e}')