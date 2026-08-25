from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.wallet import WalletTransaction
from app.models.commission import Commission
from app.security import get_current_user
from app.services.mlm_service import get_or_create_binary_volume, count_total_network_members
from app.services.wallet_service import get_or_create_wallet
from app.utils.responses import success_response

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, current_user.id)
    volume = get_or_create_binary_volume(db, current_user.id)
    
    direct_count = db.query(User).filter(User.sponsor_id == current_user.id).count()
    network_count = count_total_network_members(db, current_user.id)
    
    recent_txns = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id)\
        .order_by(WalletTransaction.created_at.desc()).limit(5).all()
        
    recent_comms = db.query(Commission).filter(Commission.beneficiary_id == current_user.id)\
        .order_by(Commission.created_at.desc()).limit(5).all()

    last_purchase = db.query(Purchase).filter(Purchase.user_id == current_user.id)\
        .order_by(Purchase.created_at.desc()).first()

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
            'active_package_name': last_purchase.package.name if (last_purchase and last_purchase.package) else None,
            'active_package_amount': last_purchase.amount if last_purchase else None
        },
        'recent_transactions': [t.to_dict() for t in recent_txns],
        'recent_commissions': [c.to_dict() for c in recent_comms]
    }
    return success_response(data)
