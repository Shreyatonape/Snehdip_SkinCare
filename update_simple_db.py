import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

# Remove extra columns from chat_messages table
print('=== Simplifying chat_messages table ===')
try:
    # Check if room_name column exists
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]

    if 'room_name' in columns:
        db.session.execute(text('ALTER TABLE chat_messages DROP COLUMN room_name'))
        print('✅ Dropped room_name column')

    if 'is_read' in columns:
        db.session.execute(text('ALTER TABLE chat_messages DROP COLUMN is_read'))
        print('✅ Dropped is_read column')

    db.session.commit()
    print('✅ chat_messages table simplified')

except Exception as e:
    print(f'❌ Error simplifying chat_messages: {e}')
    db.session.rollback()

# Remove extra columns from users table
print('=== Simplifying users table ===')
try:
    # Check if extra columns exist
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'is_online' in columns:
        db.session.execute(text('ALTER TABLE users DROP COLUMN is_online'))
        print('✅ Dropped is_online column')

    if 'last_seen' in columns:
        db.session.execute(text('ALTER TABLE users DROP COLUMN last_seen'))
        print('✅ Dropped last_seen column')

    db.session.commit()
    print('✅ users table simplified')

except Exception as e:
    print(f'❌ Error simplifying users table: {e}')
    db.session.rollback()

print('=== Verification ===')
inspector = db.inspect(db.engine)
if 'chat_messages' in inspector.get_table_names():
    columns = inspector.get_columns('chat_messages')
    print('chat_messages columns:', [col['name'] for col in columns])

if 'users' in inspector.get_table_names():
    columns = inspector.get_columns('users')
    print('users columns:', [col['name'] for col in columns])