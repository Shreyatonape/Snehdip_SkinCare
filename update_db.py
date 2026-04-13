import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

# Add missing columns to chat_messages table
print('=== Adding missing columns to chat_messages ===')
try:
    # Add room_name column
    db.session.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS room_name VARCHAR(50) NOT NULL DEFAULT ''"))
    print('✅ Added room_name column')

    # Add is_read column
    db.session.execute(text('ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE'))
    print('✅ Added is_read column')

    # Update existing messages with room names
    db.session.execute(text("""
        UPDATE chat_messages
        SET room_name = 'chat_' || LEAST(sender_id, receiver_id) || '_' || GREATEST(sender_id, receiver_id)
        WHERE room_name = ''
    """))
    print('✅ Updated existing messages with room names')

    db.session.commit()
    print('✅ Database schema updated successfully')

except Exception as e:
    print(f'❌ Error updating database: {e}')
    db.session.rollback()

# Add missing columns to users table
print('=== Adding missing columns to users ===')
try:
    # Add is_online column
    db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_online BOOLEAN DEFAULT FALSE'))
    print('✅ Added is_online column')

    # Add last_seen column
    db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
    print('✅ Added last_seen column')

    db.session.commit()
    print('✅ Users table updated successfully')

except Exception as e:
    print(f'❌ Error updating users table: {e}')
    db.session.rollback()

print('=== Verification ===')
inspector = db.inspect(db.engine)
if 'chat_messages' in inspector.get_table_names():
    columns = inspector.get_columns('chat_messages')
    print('chat_messages columns:', [col['name'] for col in columns])

if 'users' in inspector.get_table_names():
    columns = inspector.get_columns('users')
    print('users columns:', [col['name'] for col in columns])