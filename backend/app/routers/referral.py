from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.security import get_current_user
from app.services.mlm_service import resolve_sponsor_by_code
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/referral", tags=["referral"])

@router.get("/my-referrals")
def my_referrals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(User).filter(User.sponsor_id == current_user.id).order_by(User.created_at.desc())
    total = query.count()
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    referrals_data = []
    for u in items:
        vol = u.volume
        last_pur = db.query(Purchase).filter(Purchase.user_id == u.id).order_by(Purchase.created_at.desc()).first()
        referrals_data.append({
            'id': u.id,
            'user_code': u.user_code,
            'full_name': u.full_name,
            'email': u.email,
            'mobile': u.mobile,
            'referral_code': u.referral_code,
            'binary_parent_id': u.binary_parent_id,
            'binary_parent_name': u.binary_parent.full_name if u.binary_parent else None,
            'binary_position': u.binary_position,
            'is_active': u.is_active,
            'personal_bv': vol.personal_bv if vol else 0.0,
            'active_package': last_pur.package.name if (last_pur and last_pur.package) else ('Active' if u.is_active else 'None'),
            'joined_at': u.created_at.isoformat()
        })
        
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return success_response({
        'items': referrals_data,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'total_direct': total
    })

@router.get("/{code_or_ref}")
def lookup_referral(code_or_ref: str, db: Session = Depends(get_db)):
    code_clean = code_or_ref.strip().upper()
    user = resolve_sponsor_by_code(db, code_clean)
    if not user:
        user = db.query(User).filter(User.user_code == code_clean).first()
        
    if not user:
        return error_response("NOT_FOUND", f"Referral code '{code_or_ref}' not found.", 404)
        
    return success_response({
        'valid': True,
        'sponsor_name': user.full_name,
        'sponsor_code': user.user_code,
        'referral_code': user.referral_code,
        'is_active': user.is_active
    })
