from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.security import hash_password, verify_password, create_access_token, get_current_user
from app.services.mlm_service import (
    resolve_sponsor_by_code,
    validate_binary_placement,
    find_extreme_placement,
    auto_place_in_binary_tree,
    get_or_create_binary_volume
)
from app.services.wallet_service import get_or_create_wallet
from app.services.audit_service import log_action
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.password != req.confirm_password:
        return error_response("VALIDATION_ERROR", "Passwords do not match.", 400)
        
    # Check email and mobile uniqueness
    if db.query(User).filter(User.email == req.email.lower().strip()).first():
        return error_response("DUPLICATE_EMAIL", "An account with this email already exists.", 400)
    if db.query(User).filter(User.mobile == req.mobile.strip()).first():
        return error_response("DUPLICATE_MOBILE", "An account with this mobile number already exists.", 400)

    # 1. Resolve Sponsor
    sponsor = resolve_sponsor_by_code(db, req.referral_code)
    if not sponsor:
        return error_response("INVALID_SPONSOR", f"Referral code '{req.referral_code}' is invalid.", 400)

    # 2. Binary Placement Parent & Position (Extreme Left / Extreme Right)
    requested_position = (req.binary_position or 'LEFT').strip().upper()
    if requested_position not in ('LEFT', 'RIGHT'):
        return error_response("VALIDATION_ERROR", "Binary position must be 'LEFT' or 'RIGHT'.", 400)

    if req.binary_parent_code:
        parent = resolve_sponsor_by_code(db, req.binary_parent_code) or \
                 db.query(User).filter(User.user_code == req.binary_parent_code.strip().upper()).first()
        if not parent:
            return error_response("INVALID_PLACEMENT_PARENT", f"Placement parent code '{req.binary_parent_code}' not found.", 400)
        target_root_id = parent.id
    else:
        target_root_id = sponsor.id

    try:
        parent_id, position = find_extreme_placement(db, target_root_id, requested_position)
        validate_binary_placement(db, parent_id, position)
    except Exception as e:
        return error_response("PLACEMENT_FAILED", str(e), 400)

    user_count = db.query(User).count() + 1
    user_code = f"USR-{user_count:05d}"
    
    first_name_clean = ''.join(c for c in req.full_name.split()[0] if c.isalnum()).upper()[:5]
    if len(first_name_clean) < 3:
        first_name_clean = "MBR"
    referral_code = f"{first_name_clean}{user_count:03d}"
    
    while db.query(User).filter(User.referral_code == referral_code).first():
        user_count += 1
        referral_code = f"{first_name_clean}{user_count:03d}"

    new_user = User(
        user_code=user_code,
        email=req.email.lower().strip(),
        mobile=req.mobile.strip(),
        full_name=req.full_name.strip(),
        password_hash=hash_password(req.password),
        role='USER',
        referral_code=referral_code,
        sponsor_id=sponsor.id,
        binary_parent_id=parent_id,
        binary_position=position,
        is_active=False
    )
    db.add(new_user)
    db.flush()

    get_or_create_wallet(db, new_user.id)
    get_or_create_binary_volume(db, new_user.id)
    
    log_action(db, 'USER_REGISTERED', 'User', new_user.id, new_user.id, {
        'sponsor_code': sponsor.referral_code,
        'binary_parent_id': parent_id,
        'position': position
    })
    db.commit()

    token = create_access_token(new_user.id, new_user.role)
    return success_response({
        'token': token,
        'user': new_user.to_dict()
    }, "Account successfully registered in binary network!", 201)

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    ident = req.identifier.strip()
    user = db.query(User).filter((User.email == ident.lower()) | (User.user_code == ident.upper())).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        return error_response("INVALID_CREDENTIALS", "Invalid email/user code or password.", 401)

    token = create_access_token(user.id, user.role)
    log_action(db, 'USER_LOGIN', 'User', user.id, user.id)
    db.commit()

    return success_response({
        'token': token,
        'user': user.to_dict()
    }, "Login successful.")

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(current_user.to_dict())
