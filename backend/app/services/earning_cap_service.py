from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.config import settings
from app.models.user import User
from app.models.package import Package
from app.models.commission import Commission
from app.models.wallet import WalletTransaction
from app.models.earning_cycle import EarningCycle
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action
from app.services.time_service import time_provider

def get_or_create_active_cycle(db: Session, user_id: int, for_update: bool = False) -> EarningCycle:
    """
    Retrieves or creates the user's active/current EarningCycle with row-level locking.
    """
    query = db.query(EarningCycle).filter(
        EarningCycle.user_id == user_id,
        EarningCycle.status.in_(['ACTIVE', 'RETOPUP_REQUIRED'])
    ).order_by(EarningCycle.cycle_number.desc())
    
    if for_update:
        query = query.with_for_update()
        
    cycle = query.first()
    if not cycle:
        current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
        
        # Check highest past cycle number for this user
        last_cycle = db.query(EarningCycle).filter(
            EarningCycle.user_id == user_id
        ).order_by(EarningCycle.cycle_number.desc()).first()
        
        next_cycle_num = (last_cycle.cycle_number + 1) if last_cycle else 1
        
        # Find active user package if any
        user = db.get(User, user_id)
        package = db.query(Package).filter(Package.is_active == True).first()
        
        cycle = EarningCycle(
            user_id=user_id,
            package_id=package.id if package else None,
            cycle_number=next_cycle_num,
            direct_income=0.0,
            pairing_income=0.0,
            total_eligible_income=0.0,
            earning_cap=getattr(settings, 'EARNING_CAP_LIMIT', 300000.0),
            status='ACTIVE',
            started_at=current_ist,
            created_at=current_ist,
            updated_at=current_ist
        )
        db.add(cycle)
        db.flush()
        
        if user and user.earning_status != 'ACTIVE':
            user.earning_status = 'ACTIVE'
            db.flush()
            
    return cycle

def activate_or_renew_earning_cycle(db: Session, user_id: int, package_id: Optional[int] = None) -> EarningCycle:
    """
    Called upon successful package purchase or Security PIN package activation.
    If the user has an existing cycle, marks it COMPLETED and starts Cycle N+1 at ₹0.
    Resets user.earning_status to ACTIVE.
    Lifetime earnings are preserved.
    """
    current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
    user = db.get(User, user_id)
    
    # Query active/current cycle with row lock
    existing_cycle = db.query(EarningCycle).filter(
        EarningCycle.user_id == user_id,
        EarningCycle.status.in_(['ACTIVE', 'RETOPUP_REQUIRED'])
    ).order_by(EarningCycle.cycle_number.desc()).with_for_update().first()
    
    if existing_cycle:
        # Complete existing cycle
        existing_cycle.status = 'COMPLETED'
        existing_cycle.reset_at = current_ist
        existing_cycle.updated_at = current_ist
        next_cycle_number = existing_cycle.cycle_number + 1
        db.flush()
    else:
        last_cycle = db.query(EarningCycle).filter(
            EarningCycle.user_id == user_id
        ).order_by(EarningCycle.cycle_number.desc()).first()
        next_cycle_number = (last_cycle.cycle_number + 1) if last_cycle else 1

    new_cycle = EarningCycle(
        user_id=user_id,
        package_id=package_id,
        cycle_number=next_cycle_number,
        direct_income=0.0,
        pairing_income=0.0,
        total_eligible_income=0.0,
        earning_cap=getattr(settings, 'EARNING_CAP_LIMIT', 300000.0),
        status='ACTIVE',
        started_at=current_ist,
        created_at=current_ist,
        updated_at=current_ist
    )
    db.add(new_cycle)
    
    if user:
        user.earning_status = 'ACTIVE'
        
    db.flush()
    
    log_action(db, 'EARNING_CYCLE_RENEWED', 'EarningCycle', new_cycle.id, user_id, {
        'cycle_number': new_cycle.cycle_number,
        'earning_cap': new_cycle.earning_cap,
        'package_id': package_id,
        'previous_cycle_completed': existing_cycle.id if existing_cycle else None
    })
    
    return new_cycle

def apply_commission_with_cap(
    db: Session,
    user_id: int,
    commission_type: str,
    requested_amount: float,
    source_user_id: Optional[int] = None,
    purchase_id: Optional[int] = None,
    slot_id: Optional[str] = None,
    bv_basis: float = 0.0,
    percentage: float = 0.0,
    calculation_details: Optional[dict] = None,
    wallet_category: str = 'DIRECT_COMMISSION',
    description: str = 'Commission Credit',
    reference_id: Optional[str] = None
) -> Tuple[Commission, Optional[WalletTransaction], Dict[str, Any]]:
    """
    Transaction-safe, concurrency-locked earning cap enforcement engine.
    
    Rules:
    1. Locks active EarningCycle row using FOR UPDATE.
    2. Determines eligible remaining capacity (₹3,00,000 - total_eligible_income).
    3. If user is in RETOPUP_REQUIRED or remaining capacity == 0:
       - Allowed credit = ₹0
       - Blocked amount = requested_amount
       - Commission record created with amount=0, blocked_amount=requested_amount, is_capped=True
       - Wallet is NOT credited
    4. If remaining capacity > 0:
       - Allowed credit = min(requested_amount, remaining_capacity)
       - Blocked amount = requested_amount - allowed_credit
       - If blocked_amount > 0 or total_eligible reaches cap:
         status becomes RETOPUP_REQUIRED and capped_at timestamp is set.
       - Commission record created with credited amount and blocked amount.
       - Wallet credited for allowed amount only.
    """
    if requested_amount <= 0:
        raise ValueError("Requested commission amount must be strictly positive.")

    current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
    user = db.get(User, user_id)
    
    # 1. Acquire row lock on active EarningCycle
    cycle = get_or_create_active_cycle(db, user_id, for_update=True)
    
    cap_limit = cycle.earning_cap
    current_earned = cycle.total_eligible_income
    remaining_capacity = max(0.0, round(cap_limit - current_earned, 2))
    
    allowed_amount = min(requested_amount, remaining_capacity)
    blocked_amount = round(requested_amount - allowed_amount, 2)
    is_capped = (blocked_amount > 0) or (cycle.status == 'RETOPUP_REQUIRED')
    
    cap_reason = None
    if cycle.status == 'RETOPUP_REQUIRED' or remaining_capacity <= 0:
        cap_reason = f"Earning cap of ₹{cap_limit:,.0f} reached. Re-topup required."
        allowed_amount = 0.0
        blocked_amount = requested_amount
        is_capped = True
    elif blocked_amount > 0:
        cap_reason = f"Partial credit: ₹{allowed_amount:,.0f} credited. ₹{blocked_amount:,.0f} blocked at ₹{cap_limit:,.0f} cap."
    
    # 2. Update cycle totals if allowed_amount > 0
    if allowed_amount > 0:
        if commission_type in ['DIRECT_REFERRAL', 'DIRECT_COMMISSION']:
            cycle.direct_income = round(cycle.direct_income + allowed_amount, 2)
        elif commission_type in ['PAIR_BONUS', 'PAIRING_COMMISSION']:
            cycle.pairing_income = round(cycle.pairing_income + allowed_amount, 2)
            
        cycle.total_eligible_income = round(cycle.direct_income + cycle.pairing_income, 2)
        cycle.updated_at = current_ist
        
    # Check if cycle reached or exceeded cap
    if cycle.total_eligible_income >= cap_limit:
        cycle.status = 'RETOPUP_REQUIRED'
        if not cycle.capped_at:
            cycle.capped_at = current_ist
        if user:
            user.earning_status = 'RETOPUP_REQUIRED'
            
    db.flush()
    
    # 3. Prepare calculation details dictionary with capping metadata
    calc_details = dict(calculation_details or {})
    calc_details.update({
        'earning_cap_limit': cap_limit,
        'cycle_number': cycle.cycle_number,
        'cycle_total_before': current_earned,
        'cycle_total_after': cycle.total_eligible_income,
        'requested_amount': requested_amount,
        'credited_amount': allowed_amount,
        'blocked_amount': blocked_amount,
        'is_capped': is_capped,
        'cap_reason': cap_reason,
        'cycle_status': cycle.status
    })
    
    # 4. Insert Commission record
    comm = Commission(
        beneficiary_id=user_id,
        source_user_id=source_user_id,
        purchase_id=purchase_id,
        commission_type=commission_type,
        slot_id=slot_id,
        amount=allowed_amount,
        requested_amount=requested_amount,
        blocked_amount=blocked_amount,
        is_capped=is_capped,
        cap_reason=cap_reason,
        bv_basis=bv_basis,
        percentage=percentage,
        created_at=current_ist,
        _calculation_details=None
    )
    comm.calculation_details = calc_details
    db.add(comm)
    db.flush()
    
    # 5. Credit Wallet ledger if allowed_amount > 0
    wallet_txn = None
    if allowed_amount > 0:
        wallet_txn = credit_wallet(
            db=db,
            user_id=user_id,
            amount=allowed_amount,
            category=wallet_category,
            description=description,
            reference_id=reference_id,
            slot_id=slot_id
        )
        
    # 6. Audit Trail Logging
    log_action(db, 'COMMISSION_PROCESSED_WITH_CAP', 'Commission', comm.id, user_id, {
        'commission_type': commission_type,
        'requested_amount': requested_amount,
        'allowed_amount': allowed_amount,
        'blocked_amount': blocked_amount,
        'is_capped': is_capped,
        'cycle_number': cycle.cycle_number,
        'cycle_status': cycle.status,
        'wallet_txn_id': wallet_txn.id if wallet_txn else None
    })
    
    summary = {
        'commission_id': comm.id,
        'requested_amount': requested_amount,
        'allowed_amount': allowed_amount,
        'blocked_amount': blocked_amount,
        'is_capped': is_capped,
        'cycle_number': cycle.cycle_number,
        'cycle_total': cycle.total_eligible_income,
        'cycle_status': cycle.status,
        'remaining_capacity': cycle.remaining_capacity,
        'wallet_txn_id': wallet_txn.id if wallet_txn else None
    }
    
    return comm, wallet_txn, summary

def get_user_earning_cap_overview(db: Session, user_id: int) -> dict:
    """
    Returns the comprehensive earning cap status and metrics for the specified user.
    """
    cycle = get_or_create_active_cycle(db, user_id, for_update=False)
    user = db.get(User, user_id)
    
    # Calculate lifetime eligible Direct + Pairing income across all cycles
    lifetime_eligible = db.query(func.coalesce(func.sum(EarningCycle.total_eligible_income), 0.0)).filter(
        EarningCycle.user_id == user_id
    ).scalar() or 0.0
    
    # Calculate lifetime blocked amount
    lifetime_blocked = db.query(func.coalesce(func.sum(Commission.blocked_amount), 0.0)).filter(
        Commission.beneficiary_id == user_id,
        Commission.is_capped == True
    ).scalar() or 0.0
    
    # Past completed cycles count
    completed_cycles_count = db.query(EarningCycle).filter(
        EarningCycle.user_id == user_id,
        EarningCycle.status == 'COMPLETED'
    ).count()

    is_retopup_required = (cycle.status == 'RETOPUP_REQUIRED') or (cycle.total_eligible_income >= cycle.earning_cap)

    return {
        'user_id': user_id,
        'user_name': user.full_name if user else None,
        'user_code': user.user_code if user else None,
        'earning_status': user.earning_status if user else 'ACTIVE',
        'current_cycle': cycle.to_dict(),
        'cycle_number': cycle.cycle_number,
        'direct_income': cycle.direct_income,
        'pairing_income': cycle.pairing_income,
        'total_eligible_income': cycle.total_eligible_income,
        'earning_cap': cycle.earning_cap,
        'remaining_capacity': cycle.remaining_capacity,
        'progress_percentage': cycle.progress_percentage,
        'status': cycle.status,
        'is_retopup_required': is_retopup_required,
        'started_at': cycle.started_at.isoformat() if cycle.started_at else None,
        'capped_at': cycle.capped_at.isoformat() if cycle.capped_at else None,
        'lifetime_eligible_income': lifetime_eligible,
        'lifetime_blocked_amount': lifetime_blocked,
        'completed_cycles_count': completed_cycles_count,
        'retopup_message': (
            "Your current earning cycle has reached the ₹3,00,000 limit. "
            "Please purchase/renew the qualifying package to activate your next earning cycle."
            if is_retopup_required else None
        )
    }

def get_admin_earning_caps(
    db: Session,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    Returns paginated user earning cap cycles for the Admin dashboard.
    Filters: ALL, ACTIVE, NEAR_CAP (>=80%), CAP_REACHED, RETOPUP_REQUIRED.
    """
    query = db.query(EarningCycle).join(User, User.id == EarningCycle.user_id)
    
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.user_code.ilike(search_term),
                User.email.ilike(search_term),
                User.mobile.ilike(search_term)
            )
        )
        
    if status_filter:
        flt = status_filter.upper()
        if flt == 'ACTIVE':
            query = query.filter(EarningCycle.status == 'ACTIVE', EarningCycle.total_eligible_income < EarningCycle.earning_cap * 0.8)
        elif flt == 'NEAR_CAP':
            query = query.filter(
                EarningCycle.status == 'ACTIVE',
                EarningCycle.total_eligible_income >= EarningCycle.earning_cap * 0.8,
                EarningCycle.total_eligible_income < EarningCycle.earning_cap
            )
        elif flt in ['CAP_REACHED', 'RETOPUP_REQUIRED']:
            query = query.filter(
                or_(
                    EarningCycle.status == 'RETOPUP_REQUIRED',
                    EarningCycle.total_eligible_income >= EarningCycle.earning_cap
                )
            )
        elif flt == 'COMPLETED':
            query = query.filter(EarningCycle.status == 'COMPLETED')
            
    total_count = query.count()
    cycles = query.order_by(EarningCycle.updated_at.desc()).offset(offset).limit(limit).all()
    
    # Summary statistics
    total_active = db.query(EarningCycle).filter(EarningCycle.status == 'ACTIVE').count()
    total_retopup_required = db.query(EarningCycle).filter(
        or_(
            EarningCycle.status == 'RETOPUP_REQUIRED',
            EarningCycle.total_eligible_income >= EarningCycle.earning_cap
        )
    ).count()
    total_near_cap = db.query(EarningCycle).filter(
        EarningCycle.status == 'ACTIVE',
        EarningCycle.total_eligible_income >= EarningCycle.earning_cap * 0.8,
        EarningCycle.total_eligible_income < EarningCycle.earning_cap
    ).count()

    return {
        'items': [c.to_dict() for c in cycles],
        'total': total_count,
        'limit': limit,
        'offset': offset,
        'summary': {
            'total_active_cycles': total_active,
            'total_retopup_required': total_retopup_required,
            'total_near_cap': total_near_cap,
            'cap_limit': getattr(settings, 'EARNING_CAP_LIMIT', 300000.0)
        }
    }

def admin_override_reset_cycle(
    db: Session,
    user_id: int,
    admin_id: int,
    reason: str,
    new_cap: Optional[float] = None
) -> EarningCycle:
    """
    Permission-protected Admin override to complete the current cycle and start a new one.
    Mandatory reason required for full auditability.
    """
    if not reason or len(reason.strip()) < 5:
        raise ValueError("A mandatory audit reason (minimum 5 characters) is required for admin earning cap override.")

    current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found.")

    active_cycle = db.query(EarningCycle).filter(
        EarningCycle.user_id == user_id,
        EarningCycle.status.in_(['ACTIVE', 'RETOPUP_REQUIRED'])
    ).order_by(EarningCycle.cycle_number.desc()).with_for_update().first()

    old_cycle_id = None
    old_cycle_num = 0
    if active_cycle:
        active_cycle.status = 'COMPLETED'
        active_cycle.reset_at = current_ist
        old_cycle_id = active_cycle.id
        old_cycle_num = active_cycle.cycle_number

    cap_value = new_cap if (new_cap and new_cap > 0) else getattr(settings, 'EARNING_CAP_LIMIT', 300000.0)
    
    new_cycle = EarningCycle(
        user_id=user_id,
        package_id=active_cycle.package_id if active_cycle else None,
        cycle_number=old_cycle_num + 1,
        direct_income=0.0,
        pairing_income=0.0,
        total_eligible_income=0.0,
        earning_cap=cap_value,
        status='ACTIVE',
        started_at=current_ist,
        created_at=current_ist,
        updated_at=current_ist
    )
    db.add(new_cycle)
    user.earning_status = 'ACTIVE'
    db.flush()

    log_action(db, 'ADMIN_EARNING_CAP_OVERRIDE_RESET', 'EarningCycle', new_cycle.id, admin_id, {
        'user_id': user_id,
        'user_code': user.user_code,
        'admin_id': admin_id,
        'reason': reason.strip(),
        'previous_cycle_id': old_cycle_id,
        'new_cycle_number': new_cycle.cycle_number,
        'new_cap': cap_value
    })

    return new_cycle
