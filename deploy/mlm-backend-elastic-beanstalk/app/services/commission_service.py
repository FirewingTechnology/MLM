from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.commission import Commission
from app.models.volume_ledger import VolumeLedger
from app.services.mlm_service import get_or_create_binary_volume, get_binary_ancestors
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action
from app.services.time_service import time_provider, slot_service
from app.services.pair_service import pair_service
from app.services.earning_cap_service import apply_commission_with_cap, activate_or_renew_earning_cycle

class CommissionProcessingError(Exception):
    pass

def process_package_purchase(
    db: Session,
    user_id: int,
    package_id: int = None,
    idempotency_key: str = None,
    slot_id: str = None
) -> tuple[Purchase, list[dict]]:
    user = db.get(User, user_id)
    if not user:
        raise CommissionProcessingError("User not found.")
        
    # Check idempotency on purchase
    if idempotency_key:
        existing = db.query(Purchase).filter(Purchase.idempotency_key == idempotency_key).first()
        if existing:
            return existing, [{'type': 'IDEMPOTENT_REPLAY', 'message': 'Purchase already processed'}]

    # Fetch package
    if package_id:
        package = db.get(Package, package_id)
    else:
        package = db.query(Package).filter(Package.is_active == True).first()
        
    if not package:
        raise CommissionProcessingError("No active package available.")
        
    current_ist = time_provider.get_current_ist_time(db)
    slot_id = slot_id or slot_service.get_slot_id(current_ist)
    purchase_code = f"PUR-{abs(hash(f'{user_id}-{current_ist.timestamp()}')) % 1000000000:09d}"
    
    purchase = Purchase(
        purchase_code=purchase_code,
        user_id=user.id,
        package_id=package.id,
        amount=package.price,
        product_value=package.product_value,
        gst_amount=package.gst_amount,
        bv=package.bv,
        status='COMPLETED',
        slot_id=slot_id,
        idempotency_key=idempotency_key,
        created_at=current_ist.replace(tzinfo=None)
    )
    db.add(purchase)
    db.flush()
    
    # 1. Activate user, add personal BV & activate/renew earning cycle
    user.is_active = True
    user_vol = get_or_create_binary_volume(db, user.id)
    user_vol.personal_bv += package.bv
    
    # Renew / activate earning cycle (Cycle N+1, reset counter to ₹0, remove RETOPUP_REQUIRED)
    activate_or_renew_earning_cycle(db, user_id=user.id, package_id=package.id)
    
    events_triggered = []
    
    # 2. Process Direct Sponsor Commission (10% on BV) with ₹3,00,000 Earning Cap
    # Strictly to user.sponsor_id ONLY (never placement parent unless sponsor == placement parent)
    if user.sponsor_id:
        sponsor = db.get(User, user.sponsor_id)
        if sponsor:
            # Check duplicate commission for idempotency
            existing_direct = db.query(Commission).filter(
                Commission.purchase_id == purchase.id,
                Commission.beneficiary_id == sponsor.id,
                Commission.commission_type == 'DIRECT_REFERRAL'
            ).first()
            
            if not existing_direct:
                direct_bonus = package.bv * settings.DIRECT_COMMISSION_RATE
                
                calc_details = {
                    'trigger': 'DIRECT_REFERRAL',
                    'slot_id': slot_id,
                    'source_user': {'id': user.id, 'name': user.full_name, 'code': user.user_code},
                    'package': {'name': package.name, 'price': package.price, 'bv': package.bv},
                    'percentage': settings.DIRECT_COMMISSION_RATE * 100.0,
                    'bv_basis': package.bv,
                    'earned_amount': direct_bonus,
                    'explanation': (
                        f"10% Direct Referral Commission on {package.bv:,.0f} BV from "
                        f"{user.full_name}'s purchase of {package.name} (Slot: {slot_id})."
                    )
                }
                
                comm, wallet_txn, cap_summary = apply_commission_with_cap(
                    db=db,
                    user_id=sponsor.id,
                    commission_type='DIRECT_REFERRAL',
                    requested_amount=direct_bonus,
                    source_user_id=user.id,
                    purchase_id=purchase.id,
                    slot_id=slot_id,
                    bv_basis=package.bv,
                    percentage=settings.DIRECT_COMMISSION_RATE * 100.0,
                    calculation_details=calc_details,
                    wallet_category='DIRECT_COMMISSION',
                    description=f"Direct Sponsor Bonus for {user.full_name} ({user.user_code}) [{slot_id}]",
                    reference_id=purchase.purchase_code
                )
                
                events_triggered.append({
                    'type': 'DIRECT_REFERRAL_COMMISSION',
                    'beneficiary': sponsor.full_name,
                    'beneficiary_id': sponsor.id,
                    'amount': cap_summary['allowed_amount'],
                    'requested_amount': direct_bonus,
                    'blocked_amount': cap_summary['blocked_amount'],
                    'is_capped': cap_summary['is_capped'],
                    'bv': package.bv,
                    'slot_id': slot_id
                })
            
    # 3. Matching Volume Traceable Propagation & Ancestor Volume Ledger
    ancestors = get_binary_ancestors(db, user.id)
    
    for ancestor, leg_position in ancestors:
        # Idempotency check: prevent duplicate BV propagation for same purchase + ancestor
        existing_ledger = db.query(VolumeLedger).filter(
            VolumeLedger.purchase_id == purchase.id,
            VolumeLedger.ancestor_user_id == ancestor.id
        ).first()
        if existing_ledger:
            continue

        # Create ancestor-specific immutable VolumeLedger entry
        vol_entry = VolumeLedger(
            source_user_id=user.id,
            ancestor_user_id=ancestor.id,
            side=leg_position,
            purchase_id=purchase.id,
            source_reference=purchase.purchase_code,
            slot_id=slot_id,
            amount=package.bv,
            consumed_amount=0.0,
            remaining_amount=package.bv,
            status='ACTIVE',
            created_at=current_ist.replace(tzinfo=None)
        )
        db.add(vol_entry)
        db.flush()

        anc_vol = get_or_create_binary_volume(db, ancestor.id)
        
        # Credit lifetime accumulated leg volume
        if leg_position == 'LEFT':
            anc_vol.accumulated_left_bv += package.bv
        elif leg_position == 'RIGHT':
            anc_vol.accumulated_right_bv += package.bv
            
        # Record period volume and evaluate 30k/30k Matching Pair Bonus (max 1 pair per slot)
        pair_event = pair_service.record_bv_and_evaluate_pairs(
            db=db,
            user_id=ancestor.id,
            leg=leg_position,
            bv_amount=package.bv,
            slot_id=slot_id,
            purchase_id=purchase.id,
            source_user_id=user.id,
            created_at=current_ist.replace(tzinfo=None)
        )
        
        # Keep base BinaryVolume carry in sync with period volume ending carry
        period_vol = pair_service.get_or_create_period_volume(db, ancestor.id, slot_id)
        anc_vol.carry_left_bv = period_vol.ending_carry_left
        anc_vol.carry_right_bv = period_vol.ending_carry_right
        if period_vol.pair_completed:
            anc_vol.matched_bv += period_vol.consumed_left_bv

        events_triggered.append({
            'type': 'BV_BUBBLED',
            'beneficiary': ancestor.full_name,
            'beneficiary_id': ancestor.id,
            'leg': leg_position,
            'bv_added': package.bv,
            'effective_left': period_vol.effective_left_bv,
            'effective_right': period_vol.effective_right_bv,
            'ending_carry_left': period_vol.ending_carry_left,
            'ending_carry_right': period_vol.ending_carry_right,
            'slot_id': slot_id
        })
        
        if pair_event:
            events_triggered.append(pair_event)

    # 4. Evaluate Rank & Reward Advancements for Sponsor & Upward Network
    try:
        from app.services.rank_service import evaluate_ranks_on_user_activation
        evaluate_ranks_on_user_activation(db, user.id)
    except Exception as e:
        print(f"[Warning] Rank evaluation notice on user {user.id} activation: {e}")

    log_action(db, 'PACKAGE_PURCHASED', 'Purchase', purchase.id, user.id, {
        'package': package.name,
        'amount': package.price,
        'bv': package.bv,
        'slot_id': slot_id,
        'events_count': len(events_triggered)
    })
    
    return purchase, events_triggered
