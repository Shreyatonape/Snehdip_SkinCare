from flask import Flask, request
from functools import wraps
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret'

def token_required(f):
    """JWT authentication decorator for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return {"error": "Invalid token format"}, 401

        if not token:
            return {"error": "Token is missing"}, 401

        try:
            # Decode JWT token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

            # Support both payload.id and payload.user_id for frontend compatibility
            current_user_id = payload.get('user_id') or payload.get('id')
            current_role = payload.get('role')

            if not current_user_id or not current_role:
                return {"error": "Invalid token payload"}, 401

            # Add to request context
            request.current_user_id = current_user_id
            request.current_role = current_role
            request.is_admin = payload.get('is_admin', False)
            request.is_approved = payload.get('is_approved', False)

            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401

    return decorated

@app.route("/test")
@token_required
def test_route():
    return {"success": True, "message": "Decorator working!"}

if __name__ == "__main__":
    with app.test_request_context():
        print("✅ Minimal test successful!")