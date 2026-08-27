from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.wallet import WalletTransaction
from app.models.commission import Commission
from app.security import get_current_user
from app.services.mlm_service import get_or_create_binary_volume, count_total_network_members
from app.services.wallet_service import get_or_create_wallet
from app.services.time_service import time_provider
from app.services.pair_service import pair_service
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

    slot_info = time_provider.get_current_slot_info(db)
    pair_summary = pair_service.get_user_pair_summary(db, current_user.id, slot_info.slot_id)

    # All-time category breakdown
    direct_total = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])).scalar() or 0.0
    pair_total = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.commission_type == 'PAIR_BONUS').scalar() or 0.0
    matching_total = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])).scalar() or 0.0
    carry_total = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.commission_type == 'CARRY_COMMISSION').scalar() or 0.0

    # Current slot category breakdown
    slot_direct = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id, Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])).scalar() or 0.0
    slot_pair = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id, Commission.commission_type == 'PAIR_BONUS').scalar() or 0.0
    slot_matching = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id, Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])).scalar() or 0.0
    slot_carry = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id, Commission.commission_type == 'CARRY_COMMISSION').scalar() or 0.0

    slot_earnings = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id).scalar() or 0.0
    slot_commissions_count = db.query(Commission)\
        .filter(Commission.beneficiary_id == current_user.id, Commission.slot_id == slot_info.slot_id).count()

    data = {
        'user': current_user.to_dict(),
        'kpis': {
            'wallet_balance': wallet.balance,
            'total_earnings': wallet.total_earned,
            'total_withdrawn': wallet.total_withdrawn,
            'direct_commissions': direct_total,
            'pair_commissions': pair_total,
            'matching_commissions': matching_total,
            'carry_commissions': carry_total,
            'personal_bv': volume.personal_bv,
            'left_bv': volume.accumulated_left_bv,
            'right_bv': volume.accumulated_right_bv,
            'carry_left_bv': pair_summary['ending_carry_left'],
            'carry_right_bv': pair_summary['ending_carry_right'],
            'matched_bv': volume.matched_bv,
            'total_bv': volume.accumulated_left_bv + volume.accumulated_right_bv + volume.personal_bv,
            'direct_referrals': direct_count,
            'network_members': network_count,
            'is_active': current_user.is_active,
            'active_package_name': last_purchase.package.name if (last_purchase and last_purchase.package) else None,
            'active_package_amount': last_purchase.amount if last_purchase else None,
            'slot_earnings': slot_earnings,
            'slot_direct_commissions': slot_direct,
            'slot_pair_commissions': slot_pair,
            'slot_matching_commissions': slot_matching,
            'slot_carry_commissions': slot_carry,
            'slot_commissions_count': slot_commissions_count,
            'current_slot_id': slot_info.slot_id,
            'pair_summary': pair_summary
        },
        'pair_summary': pair_summary,
        'slot_info': slot_info.to_dict(),
        'recent_transactions': [t.to_dict() for t in recent_txns],
        'recent_commissions': [c.to_dict() for c in recent_comms]
    }
    return success_response(data)

