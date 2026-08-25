from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.commission import Commission
from app.services.mlm_service import get_or_create_binary_volume, get_binary_ancestors
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action

class CommissionProcessingError(Exception):
    pass

def process_package_purchase(db: Session, user_id: int, package_id: int = None, idempotency_key: str = None) -> tuple[Purchase, list[dict]]:
    user = db.get(User, user_id)
    if not user:
        raise CommissionProcessingError("User not found.")
        
    # Check idempotency
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
        
    purchase_code = f"PUR-{abs(hash(f'{user_id}-{datetime.utcnow().timestamp()}')) % 1000000000:09d}"
    
    purchase = Purchase(
        purchase_code=purchase_code,
        user_id=user.id,
        package_id=package.id,
        amount=package.price,
        product_value=package.product_value,
        gst_amount=package.gst_amount,
        bv=package.bv,
        status='COMPLETED',
        idempotency_key=idempotency_key
    )
    db.add(purchase)
    db.flush()
    
    # 1. Activate user & add personal BV
    user.is_active = True
    user_vol = get_or_create_binary_volume(db, user.id)
    user_vol.personal_bv += package.bv
    
    events_triggered = []
    
    # 2. Process Direct Sponsor Commission (10% on BV)
    if user.sponsor_id:
        sponsor = db.get(User, user.sponsor_id)
        if sponsor:
            direct_bonus = package.bv * settings.DIRECT_REFERRAL_COMMISSION_PCT
            
            calc_details = {
                'trigger': 'DIRECT_REFERRAL',
                'source_user': {'id': user.id, 'name': user.full_name, 'code': user.user_code},
                'package': {'name': package.name, 'price': package.price, 'bv': package.bv},
                'percentage': settings.DIRECT_REFERRAL_COMMISSION_PCT * 100,
                'bv_basis': package.bv,
                'earned_amount': direct_bonus,
                'explanation': f"10% Direct Referral Commission on {package.bv:,.0f} BV from {user.full_name}'s purchase of {package.name}."
            }
            
            comm = Commission(
                beneficiary_id=sponsor.id,
                source_user_id=user.id,
                purchase_id=purchase.id,
                commission_type='DIRECT_REFERRAL',
                amount=direct_bonus,
                bv_basis=package.bv,
                percentage=settings.DIRECT_REFERRAL_COMMISSION_PCT * 100,
                _calculation_details=None
            )
            comm.calculation_details = calc_details
            db.add(comm)
            db.flush()
            
            credit_wallet(
                db,
                user_id=sponsor.id,
                amount=direct_bonus,
                category='DIRECT_COMMISSION',
                description=f"Direct Sponsor Bonus for {user.full_name} ({user.user_code})",
                reference_id=purchase.purchase_code
            )
            
            events_triggered.append({
                'type': 'DIRECT_REFERRAL_COMMISSION',
                'beneficiary': sponsor.full_name,
                'amount': direct_bonus,
                'bv': package.bv
            })
            
    # 3. Binary Volume Upward Bubbling & Matching Commission
    ancestors = get_binary_ancestors(db, user.id)
    
    for ancestor, leg_position in ancestors:
        anc_vol = get_or_create_binary_volume(db, ancestor.id)
        
        # Credit leg volume
        if leg_position == 'LEFT':
            anc_vol.accumulated_left_bv += package.bv
            anc_vol.carry_left_bv += package.bv
        elif leg_position == 'RIGHT':
            anc_vol.accumulated_right_bv += package.bv
            anc_vol.carry_right_bv += package.bv
            
        events_triggered.append({
            'type': 'BV_BUBBLED',
            'beneficiary': ancestor.full_name,
            'leg': leg_position,
            'bv_added': package.bv,
            'carry_left': anc_vol.carry_left_bv,
            'carry_right': anc_vol.carry_right_bv
        })
        
        # Calculate matching commission if ancestor is active
        if ancestor.is_active:
            matched_pair_bv = min(anc_vol.carry_left_bv, anc_vol.carry_right_bv)
            
            if matched_pair_bv > 0:
                matching_bonus = matched_pair_bv * settings.BINARY_MATCHING_COMMISSION_PCT
                
                anc_vol.matched_bv += matched_pair_bv
                if settings.CARRY_FORWARD_ENABLED:
                    anc_vol.carry_left_bv -= matched_pair_bv
                    anc_vol.carry_right_bv -= matched_pair_bv
                else:
                    anc_vol.carry_left_bv = 0.0
                    anc_vol.carry_right_bv = 0.0
                    
                calc_details = {
                    'trigger': 'BINARY_MATCHING',
                    'source_user': {'id': user.id, 'name': user.full_name, 'code': user.user_code},
                    'matched_bv': matched_pair_bv,
                    'percentage': settings.BINARY_MATCHING_COMMISSION_PCT * 100,
                    'earned_amount': matching_bonus,
                    'remaining_carry_left': anc_vol.carry_left_bv,
                    'remaining_carry_right': anc_vol.carry_right_bv,
                    'explanation': f"10% Binary Matching Bonus on {matched_pair_bv:,.0f} matched BV. Remaining carry: L: {anc_vol.carry_left_bv:,.0f}, R: {anc_vol.carry_right_bv:,.0f}."
                }
                
                bin_comm = Commission(
                    beneficiary_id=ancestor.id,
                    source_user_id=user.id,
                    purchase_id=purchase.id,
                    commission_type='BINARY_MATCHING',
                    amount=matching_bonus,
                    bv_basis=matched_pair_bv,
                    percentage=settings.BINARY_MATCHING_COMMISSION_PCT * 100,
                    _calculation_details=None
                )
                bin_comm.calculation_details = calc_details
                db.add(bin_comm)
                db.flush()
                
                credit_wallet(
                    db,
                    user_id=ancestor.id,
                    amount=matching_bonus,
                    category='MATCHING_COMMISSION',
                    description=f"Binary Matching Bonus on {matched_pair_bv:,.0f} Matched BV",
                    reference_id=purchase.purchase_code
                )
                
                events_triggered.append({
                    'type': 'BINARY_MATCHING_COMMISSION',
                    'beneficiary': ancestor.full_name,
                    'matched_bv': matched_pair_bv,
                    'amount': matching_bonus
                })

    log_action(db, 'PACKAGE_PURCHASED', 'Purchase', purchase.id, user.id, {
        'package': package.name,
        'amount': package.price,
        'bv': package.bv,
        'events_count': len(events_triggered)
    })
    
    return purchase, events_triggered
