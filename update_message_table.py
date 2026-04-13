import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

print('=== Update Message Table ===')

# Check if chat_messages table exists and rename it to messages
inspector = db.inspect(db.engine)
tables = inspector.get_table_names()

if 'chat_messages' in tables:
    print('Found chat_messages table, renaming to messages...')
    try:
        # Rename table from chat_messages to messages
        db.session.execute(text('ALTER TABLE chat_messages RENAME TO messages'))
        db.session.commit()
        print('✅ Successfully renamed chat_messages to messages')
    except Exception as e:
        print(f'❌ Error renaming table: {e}')
        db.session.rollback()
elif 'messages' in tables:
    print('✅ messages table already exists')
else:
    print('❌ Neither chat_messages nor messages table exists')

# Verify the final table structure
if 'messages' in inspector.get_table_names():
    columns = inspector.get_columns('messages')
    print('\nmessages table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')

    # Check if it has the correct structure
    required_columns = ['id', 'sender_id', 'receiver_id', 'message', 'timestamp']
    existing_columns = [col['name'] for col in columns]

    print('\n=== Column Verification ===')
    for col in required_columns:
        if col in existing_columns:
            print(f'✅ {col} - EXISTS')
        else:
            print(f'❌ {col} - MISSING')
else:
    print('❌ messages table not found')

print('\n=== Test Message Model ===')
try:
    from models import Message
    messages = Message.query.limit(1).all()
    print('✅ Message model works')
    if messages:
        msg = messages[0]
        print(f'✅ Sample message: {msg.message[:50]}...')
except Exception as e:
    print(f'❌ Message model error: {e}')