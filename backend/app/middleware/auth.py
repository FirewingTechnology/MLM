from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.utils.responses import error_response

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            user = db.session.get(User, int(identity))
            if not user:
                return error_response("UNAUTHORIZED", "User not found or session invalid.", 401)
            return fn(user, *args, **kwargs)
        except Exception as e:
            return error_response("UNAUTHORIZED", f"Authentication required: {str(e)}", 401)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            user = db.session.get(User, int(identity))
            if not user or user.role != 'ADMIN':
                return error_response("FORBIDDEN", "Admin privileges required for this operation.", 403)
            return fn(user, *args, **kwargs)
        except Exception as e:
            return error_response("FORBIDDEN", f"Admin access denied: {str(e)}", 403)
    return wrapper
