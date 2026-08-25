from flask import Blueprint, request
from app.models.user import User
from app.models.purchase import Purchase
from app.services.mlm_service import resolve_sponsor_by_code
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

referral_bp = Blueprint('referral', __name__, url_prefix='/api/referral')

@referral_bp.route('/<code_or_ref>', methods=['GET'])
def lookup_referral(code_or_ref):
    user = resolve_sponsor_by_code(code_or_ref)
    if not user:
        # Try matching user_code as well
        user = User.query.filter_by(user_code=code_or_ref.strip().upper()).first()
        
    if not user:
        return error_response("NOT_FOUND", f"Referral code '{code_or_ref}' not found.", 404)
        
    return success_response({
        'valid': True,
        'sponsor_name': user.full_name,
        'sponsor_code': user.user_code,
        'referral_code': user.referral_code,
        'is_active': user.is_active
    })

@referral_bp.route('/my-referrals', methods=['GET'])
@token_required
def my_referrals(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = current_user.sponsored_users.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    referrals_data = []
    for u in pagination.items:
        vol = u.volume
        last_pur = u.purchases.order_by(Purchase.created_at.desc()).first()
        referrals_data.append({
            'id': u.id,
            'user_code': u.user_code,
            'full_name': u.full_name,
            'email': u.email,
            'mobile': u.mobile,
            'is_active': u.is_active,
            'binary_parent_name': u.binary_parent.full_name if u.binary_parent else None,
            'binary_position': u.binary_position,
            'package_name': last_pur.package.name if last_pur and last_pur.package else None,
            'personal_bv': vol.personal_bv if vol else 0,
            'joined_at': u.created_at.isoformat()
        })

    return success_response({
        'items': referrals_data,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'total_direct': current_user.sponsored_users.count()
    })
