from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.extensions import db, hash_password, check_password
from app.models.user import User
from app.services.mlm_service import (
    resolve_sponsor_by_code, 
    validate_and_assign_placement, 
    get_or_create_binary_volume
)
from app.services.wallet_service import get_or_create_wallet
from app.services.audit_service import log_action
from app.utils.ids import generate_user_code, generate_referral_code
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    mobile = data.get('mobile', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    referral_code = data.get('referral_code', '').strip().upper()
    binary_parent_code = data.get('binary_parent_code', None)
    binary_position = data.get('binary_position', None)

    # Validations
    if not full_name:
        return error_response("VALIDATION_ERROR", "Full name is required.")
    if not email or '@' not in email:
        return error_response("VALIDATION_ERROR", "Valid email address is required.")
    if not mobile or len(mobile) < 7:
        return error_response("VALIDATION_ERROR", "Valid mobile number is required.")
    if not password or len(password) < 6:
        return error_response("VALIDATION_ERROR", "Password must be at least 6 characters long.")
    if password != confirm_password:
        return error_response("VALIDATION_ERROR", "Passwords do not match.")

    if User.query.filter_by(email=email).first():
        return error_response("DUPLICATE_EMAIL", "An account with this email already exists.")
    if User.query.filter_by(mobile=mobile).first():
        return error_response("DUPLICATE_MOBILE", "An account with this mobile number already exists.")

    sponsor = None
    if referral_code:
        sponsor = resolve_sponsor_by_code(referral_code)
        if not sponsor:
            return error_response("INVALID_REFERRAL", f"Referral code '{referral_code}' is invalid or does not exist.")
    else:
        # Check if root user exists
        root_count = User.query.count()
        if root_count > 0:
            return error_response("REFERRAL_REQUIRED", "Referral code is mandatory for registration.")

    # Generate unique user code and referral code
    next_id = (User.query.order_by(User.id.desc()).first().id + 1) if User.query.first() else 1
    user_code = generate_user_code(next_id)
    new_referral_code = generate_referral_code(full_name)
    while User.query.filter_by(referral_code=new_referral_code).first():
        new_referral_code = generate_referral_code(full_name)

    new_user = User(
        user_code=user_code,
        email=email,
        mobile=mobile,
        full_name=full_name,
        password_hash=hash_password(password),
        role='USER',
        referral_code=new_referral_code,
        is_active=False
    )

    try:
        validate_and_assign_placement(
            new_user=new_user,
            sponsor=sponsor,
            binary_parent_code=binary_parent_code,
            binary_position=binary_position
        )
    except Exception as e:
        return error_response("PLACEMENT_ERROR", str(e))

    db.session.add(new_user)
    db.session.flush()

    # Initialize wallet and volume
    get_or_create_wallet(new_user.id)
    get_or_create_binary_volume(new_user.id)

    log_action('USER_REGISTERED', 'User', new_user.user_code, new_user.id, {
        'sponsor_id': new_user.sponsor_id,
        'binary_parent_id': new_user.binary_parent_id,
        'position': new_user.binary_position
    }, request.remote_addr)

    db.session.commit()

    # Generate token
    token = create_access_token(identity=str(new_user.id))

    return success_response({
        'token': token,
        'user': new_user.to_dict()
    }, "Registration successful! Welcome to the Demo Binary MLM platform.", 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()  # Can be email, user_code, or referral_code
    password = data.get('password', '')

    if not identifier or not password:
        return error_response("VALIDATION_ERROR", "Login identifier and password are required.")

    user = None
    if '@' in identifier:
        user = User.query.filter_by(email=identifier.lower()).first()
    else:
        user = User.query.filter_by(user_code=identifier.upper()).first()
        if not user:
            user = User.query.filter_by(referral_code=identifier.upper()).first()

    if not user or not check_password(password, user.password_hash):
        return error_response("INVALID_CREDENTIALS", "Invalid login credentials. Please check and try again.", 401)

    token = create_access_token(identity=str(user.id))
    log_action('USER_LOGIN', 'User', user.user_code, user.id, None, request.remote_addr)
    db.session.commit()

    return success_response({
        'token': token,
        'user': user.to_dict()
    }, "Login successful!")

@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    return success_response(current_user.to_dict())

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    return success_response(None, "Logged out successfully.")
