from flask import Blueprint
from app.models.user import User
from app.models.purchase import Purchase
from app.models.wallet import WalletTransaction
from app.models.commission import Commission
from app.services.mlm_service import get_or_create_binary_volume, count_total_network_members
from app.services.wallet_service import get_or_create_wallet
from app.utils.responses import success_response
from app.middleware.auth import token_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
@token_required
def get_dashboard(current_user):
    wallet = get_or_create_wallet(current_user.id)
    volume = get_or_create_binary_volume(current_user.id)
    
    direct_count = User.query.filter_by(sponsor_id=current_user.id).count()
    network_count = count_total_network_members(current_user.id)
    
    # Recent transactions
    recent_txns = WalletTransaction.query.filter_by(user_id=current_user.id)\
        .order_by(WalletTransaction.created_at.desc()).limit(5).all()
        
    # Recent commissions
    recent_comms = Commission.query.filter_by(beneficiary_id=current_user.id)\
        .order_by(Commission.created_at.desc()).limit(5).all()

    # Active package if any
    last_purchase = current_user.purchases.order_by(Purchase.created_at.desc()).first()

    data = {
        'user': current_user.to_dict(),
        'kpis': {
            'wallet_balance': wallet.balance,
            'total_earnings': wallet.total_earned,
            'total_withdrawn': wallet.total_withdrawn,
            'personal_bv': volume.personal_bv,
            'left_bv': volume.accumulated_left_bv,
            'right_bv': volume.accumulated_right_bv,
            'carry_left_bv': volume.carry_left_bv,
            'carry_right_bv': volume.carry_right_bv,
            'matched_bv': volume.matched_bv,
            'total_bv': volume.accumulated_left_bv + volume.accumulated_right_bv + volume.personal_bv,
            'direct_referrals': direct_count,
            'network_members': network_count,
            'is_active': current_user.is_active,
            'active_package_name': last_purchase.package.name if last_purchase and last_purchase.package else None,
            'active_package_amount': last_purchase.amount if last_purchase else 0
        },
        'sponsor': {
            'name': current_user.sponsor.full_name if current_user.sponsor else None,
            'code': current_user.sponsor.user_code if current_user.sponsor else None,
            'email': current_user.sponsor.email if current_user.sponsor else None
        },
        'placement': {
            'parent_name': current_user.binary_parent.full_name if current_user.binary_parent else None,
            'parent_code': current_user.binary_parent.user_code if current_user.binary_parent else None,
            'position': current_user.binary_position
        },
        'recent_transactions': [t.to_dict() for t in recent_txns],
        'recent_commissions': [c.to_dict() for c in recent_comms]
    }
    
    return success_response(data)
