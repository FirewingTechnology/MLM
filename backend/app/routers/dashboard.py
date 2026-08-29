from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.wallet import WalletTransaction
from app.models.commission import Commission
from app.config import settings
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.security import get_current_user
from app.services.mlm_service import get_or_create_binary_volume, count_total_network_members, get_leg_subtree_user_ids
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

    # Carry Accounting (Paid vs Unpaid BV and Pair Units) derived from real persisted ledger & settlements
    left_unpaid_bv = max(0.0, float(pair_summary.get('ending_carry_left', 0.0)))
    right_unpaid_bv = max(0.0, float(pair_summary.get('ending_carry_right', 0.0)))

    left_ledger_consumed = db.query(func.coalesce(func.sum(VolumeLedger.consumed_amount), 0.0))\
        .filter(VolumeLedger.ancestor_user_id == current_user.id, VolumeLedger.side == 'LEFT').scalar() or 0.0
    right_ledger_consumed = db.query(func.coalesce(func.sum(VolumeLedger.consumed_amount), 0.0))\
        .filter(VolumeLedger.ancestor_user_id == current_user.id, VolumeLedger.side == 'RIGHT').scalar() or 0.0

    left_settlement_matched = db.query(func.coalesce(func.sum(SlotSettlement.left_matched), 0.0))\
        .filter(SlotSettlement.user_id == current_user.id).scalar() or 0.0
    right_settlement_matched = db.query(func.coalesce(func.sum(SlotSettlement.right_matched), 0.0))\
        .filter(SlotSettlement.user_id == current_user.id).scalar() or 0.0

    total_pair_bonus_count = db.query(Commission)\
        .filter(Commission.beneficiary_id == current_user.id, Commission.commission_type == 'PAIR_BONUS').count()
    pair_bonus_consumed = total_pair_bonus_count * 30000.0

    curr_consumed_left = float(pair_summary.get('consumed_left_bv', 0.0))
    curr_consumed_right = float(pair_summary.get('consumed_right_bv', 0.0))

    left_paid_bv = max(0.0, float(left_ledger_consumed), float(left_settlement_matched), float(pair_bonus_consumed), curr_consumed_left, float(volume.matched_bv))
    right_paid_bv = max(0.0, float(right_ledger_consumed), float(right_settlement_matched), float(pair_bonus_consumed), curr_consumed_right, float(volume.matched_bv))

    left_total_bv = max(left_paid_bv + left_unpaid_bv, float(volume.accumulated_left_bv))
    right_total_bv = max(right_paid_bv + right_unpaid_bv, float(volume.accumulated_right_bv))

    left_unpaid_bv = max(0.0, left_total_bv - left_paid_bv)
    right_unpaid_bv = max(0.0, right_total_bv - right_paid_bv)

    # Retrieve leg subtree user IDs to calculate exact paid vs unpaid member counts
    left_subtree_ids = get_leg_subtree_user_ids(db, current_user.id, 'LEFT')
    right_subtree_ids = get_leg_subtree_user_ids(db, current_user.id, 'RIGHT')

    left_paid_members = db.query(User).filter(User.id.in_(left_subtree_ids), User.is_active == True).count() if left_subtree_ids else 0
    left_unpaid_members = db.query(User).filter(User.id.in_(left_subtree_ids), User.is_active == False).count() if left_subtree_ids else 0

    right_paid_members = db.query(User).filter(User.id.in_(right_subtree_ids), User.is_active == True).count() if right_subtree_ids else 0
    right_unpaid_members = db.query(User).filter(User.id.in_(right_subtree_ids), User.is_active == False).count() if right_subtree_ids else 0

    # Convert to Authoritative Carry Counts (30,000 BV units)
    pair_unit = float(settings.PAIR_VOLUME) if settings.PAIR_VOLUME > 0 else 30000.0

    left_paid_pairs = int(left_paid_bv // pair_unit)
    left_unpaid_pairs = int(left_unpaid_bv // pair_unit)
    left_carry_count = left_unpaid_pairs  # The carry count is the remaining unmatched carry units
    left_total_pairs = left_paid_pairs + left_unpaid_pairs

    right_paid_pairs = int(right_paid_bv // pair_unit)
    right_unpaid_pairs = int(right_unpaid_bv // pair_unit)
    right_carry_count = right_unpaid_pairs
    right_total_pairs = right_paid_pairs + right_unpaid_pairs

    # When members are placed in the binary tree legs, display accurate Paid vs Unpaid member counts.
    # Otherwise fall back to pair counts for direct volume testing.
    left_paid_count = left_paid_members if left_subtree_ids else left_paid_pairs
    left_unpaid_count = left_unpaid_members if left_subtree_ids else left_unpaid_pairs

    right_paid_count = right_paid_members if right_subtree_ids else right_paid_pairs
    right_unpaid_count = right_unpaid_members if right_subtree_ids else right_unpaid_pairs

    carry_data = {
        'left': {
            'bv': left_unpaid_bv,
            'count': left_carry_count,
            'carry_count': left_carry_count,
            'paid_count': left_paid_count,
            'unpaid_count': left_unpaid_count,
            'paid_members': left_paid_members,
            'unpaid_members': left_unpaid_members,
            'total_members': left_paid_members + left_unpaid_members,
            'total': left_total_bv,
            'paid': left_paid_bv,
            'unpaid': left_unpaid_bv,
            'carry': left_unpaid_bv,
            'total_pairs': left_total_pairs,
            'paid_pairs': left_paid_pairs,
            'unpaid_pairs': left_unpaid_pairs
        },
        'right': {
            'bv': right_unpaid_bv,
            'count': right_carry_count,
            'carry_count': right_carry_count,
            'paid_count': right_paid_count,
            'unpaid_count': right_unpaid_count,
            'paid_members': right_paid_members,
            'unpaid_members': right_unpaid_members,
            'total_members': right_paid_members + right_unpaid_members,
            'total': right_total_bv,
            'paid': right_paid_bv,
            'unpaid': right_unpaid_bv,
            'carry': right_unpaid_bv,
            'total_pairs': right_total_pairs,
            'paid_pairs': right_paid_pairs,
            'unpaid_pairs': right_unpaid_pairs
        }
    }

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
            'carry': carry_data,
            'carry_summary': carry_data,
            'carry_pair_summary': carry_data,
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
        'carry': carry_data,
        'carry_summary': carry_data,
        'carry_pair_summary': carry_data,
        'pair_summary': pair_summary,
        'slot_info': slot_info.to_dict(),
        'recent_transactions': [t.to_dict() for t in recent_txns],
        'recent_commissions': [c.to_dict() for c in recent_comms]
    }
    return success_response(data)

