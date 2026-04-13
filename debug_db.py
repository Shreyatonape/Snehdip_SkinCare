import sys
sys.path.append('.')
from app import app
from extensions import db
from models import User, ChatMessage
app.app_context().push()

# Check database schema
inspector = db.inspect(db.engine)
print('=== Database Schema Check ===')
if 'chat_messages' in inspector.get_table_names():
    columns = inspector.get_columns('chat_messages')
    print('chat_messages table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')
else:
    print('chat_messages table does not exist')

print('=== Users Table Check ===')
if 'users' in inspector.get_table_names():
    columns = inspector.get_columns('users')
    print('users table columns:')
    for col in columns:
        print(f'  - {col["name"]} ({col["type"]})')
else:
    print('users table does not exist')

print('=== SocketIO Check ===')
try:
    from flask_socketio import SocketIO
    print('SocketIO imported successfully')
    if hasattr(app, 'socketio'):
        print('SocketIO instance found in app')
    else:
        print('SocketIO instance NOT found in app')
except ImportError:
    print('SocketIO not installed')

print('=== App Configuration ===')
print('Flask app configured:', app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'))