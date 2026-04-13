import sys
sys.path.append('.')
from app import app
from extensions import db
from sqlalchemy import text
app.app_context().push()

print('=== Update Messages Table Schema ===')

# Check current table structure
inspector = db.inspect(db.engine)
if 'messages' in inspector.get_table_names():
    columns = inspector.get_columns('messages')
    current_columns = [col['name'] for col in columns]

    print('Current columns:', current_columns)

    # Add missing columns
    try:
        if 'sender_role' not in current_columns:
            db.session.execute(text('ALTER TABLE messages ADD COLUMN sender_role VARCHAR(20) NOT NULL DEFAULT \'patient\''))
            print('✅ Added sender_role column')

        if 'receiver_role' not in current_columns:
            db.session.execute(text('ALTER TABLE messages ADD COLUMN receiver_role VARCHAR(20) NOT NULL DEFAULT \'doctor\''))
            print('✅ Added receiver_role column')

        if 'is_deleted_by_sender' not in current_columns:
            db.session.execute(text('ALTER TABLE messages ADD COLUMN is_deleted_by_sender BOOLEAN DEFAULT FALSE'))
            print('✅ Added is_deleted_by_sender column')

        if 'is_deleted_by_receiver' not in current_columns:
            db.session.execute(text('ALTER TABLE messages ADD COLUMN is_deleted_by_receiver BOOLEAN DEFAULT FALSE'))
            print('✅ Added is_deleted_by_receiver column')

        # Rename timestamp to created_at if needed
        if 'timestamp' in current_columns and 'created_at' not in current_columns:
            db.session.execute(text('ALTER TABLE messages RENAME COLUMN timestamp TO created_at'))
            print('✅ Renamed timestamp to created_at')

        db.session.commit()
        print('✅ Messages table schema updated successfully')

    except Exception as e:
        print(f'❌ Error updating schema: {e}')
        db.session.rollback()

    # Verify final structure
    updated_columns = inspector.get_columns('messages')
    print('\nFinal messages table columns:')
    for col in updated_columns:
        print(f'  - {col["name"]} ({col["type"]})')

else:
    print('❌ messages table does not exist')

print('\n=== Update Existing Messages ===')
try:
    # Update role information for existing messages
    from models import User, Message

    messages = Message.query.all()
    updated_count = 0

    for msg in messages:
        # Get sender and receiver roles
        sender = User.query.get(msg.sender_id)
        receiver = User.query.get(msg.receiver_id)

        if sender and receiver:
            msg.sender_role = sender.role
            msg.receiver_role = receiver.role
            updated_count += 1

    if updated_count > 0:
        db.session.commit()
        print(f'✅ Updated role information for {updated_count} messages')
    else:
        print('✅ All messages already have role information')

except Exception as e:
    print(f'❌ Error updating messages: {e}')
    db.session.rollback()

print('\n=== Verification ===')
try:
    from models import Message
    messages = Message.query.limit(3).all()

    if messages:
        print('Sample messages:')
        for msg in messages:
            sender = User.query.get(msg.sender_id)
            receiver = User.query.get(msg.receiver_id)
            print(f'  {sender.username} ({msg.sender_role}) → {receiver.username} ({msg.receiver_role}): "{msg.message[:30]}..."')
    else:
        print('No messages found')

except Exception as e:
    print(f'❌ Error verifying: {e}')

print('\n✅ Messages table is ready for role-based messaging system')