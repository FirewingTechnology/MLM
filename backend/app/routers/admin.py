from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.commission import Commission
from app.models.wallet import Wallet
from app.models.withdrawal import Withdrawal
from app.models.audit_log import AuditLog
from app.models.activation_request import PackageActivationRequest
from app.models.security_pin import SecurityPin
from app.schemas.common import AdminApprovalRequest, WalletAdjustmentRequest, UserStatusRequest
from app.schemas.time_schemas import TimeModeRequest, SetTimeRequest, AdvanceTimeRequest
from app.schemas.activation import (
    AdminVerifyPaymentRequest,
    AdminIssuePinRequest,
    AdminRejectRequest,
    AdminRevokePinRequest
)
from app.security import get_current_admin
from app.services.wallet_service import approve_withdrawal, reject_withdrawal, adjust_wallet_balance
from app.services.seed_service import reset_demo_database
from app.services.time_service import time_provider, slot_service
from app.services.pin_service import pin_service, PinSecurityError
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/dashboard")
def admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = total_users - active_users
    
    total_sales = db.query(func.coalesce(func.sum(Purchase.amount), 0.0)).scalar() or 0.0
    total_packages_activated = db.query(Purchase).filter(Purchase.status == 'COMPLETED').count()
    total_bv = db.query(func.coalesce(func.sum(BinaryVolume.personal_bv), 0.0)).scalar() or 0.0
    total_left_bv = db.query(func.coalesce(func.sum(BinaryVolume.accumulated_left_bv), 0.0)).scalar() or 0.0
    total_right_bv = db.query(func.coalesce(func.sum(BinaryVolume.accumulated_right_bv), 0.0)).scalar() or 0.0
    total_left_carry = db.query(func.coalesce(func.sum(BinaryVolume.carry_left_bv), 0.0)).scalar() or 0.0
    total_right_carry = db.query(func.coalesce(func.sum(BinaryVolume.carry_right_bv), 0.0)).scalar() or 0.0
    total_matching_volume = db.query(func.coalesce(func.sum(BinaryVolume.matched_bv), 0.0)).scalar() or 0.0
    
    total_commissions = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).scalar() or 0.0
    direct_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])).scalar() or 0.0
    matching_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])).scalar() or 0.0
    pair_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type == 'PAIR_BONUS').scalar() or 0.0
    carry_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type == 'CARRY_COMMISSION').scalar() or 0.0
        
    total_wallet_balance = db.query(func.coalesce(func.sum(Wallet.balance), 0.0)).scalar() or 0.0
    total_withdrawn = db.query(func.coalesce(func.sum(Wallet.total_withdrawn), 0.0)).scalar() or 0.0
    
    pending_withdrawals_query = db.query(Withdrawal).filter(Withdrawal.status == 'PENDING')
    pending_count = pending_withdrawals_query.count()
    pending_amount = db.query(func.coalesce(func.sum(Withdrawal.amount), 0.0))\
        .filter(Withdrawal.status == 'PENDING').scalar() or 0.0
    approved_withdrawals_count = db.query(Withdrawal).filter(Withdrawal.status == 'APPROVED').count()
    rejected_withdrawals_count = db.query(Withdrawal).filter(Withdrawal.status == 'REJECTED').count()
        
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
    
    # Slot metrics
    slot_info = time_provider.get_current_slot_info(db)
    slot_purchases_sum = db.query(func.coalesce(func.sum(Purchase.amount), 0.0))\
        .filter(Purchase.slot_id == slot_info.slot_id).scalar() or 0.0
    slot_bv_sum = db.query(func.coalesce(func.sum(Purchase.bv), 0.0))\
        .filter(Purchase.slot_id == slot_info.slot_id).scalar() or 0.0
    slot_commissions_sum = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.slot_id == slot_info.slot_id).scalar() or 0.0
    slot_purchases_count = db.query(Purchase).filter(Purchase.slot_id == slot_info.slot_id).count()

    # PIN & Activation Metrics
    from app.models.pin_order import SecurityPinOrder
    from app.models.wallet import WalletTransaction
    pending_activations_count = db.query(PackageActivationRequest).filter(
        PackageActivationRequest.status.in_(['PAYMENT_SUBMITTED', 'UNDER_REVIEW'])
    ).count()
    verified_activations_count = db.query(PackageActivationRequest).filter(
        PackageActivationRequest.status == 'PAYMENT_VERIFIED'
    ).count()
    
    total_pins_count = db.query(SecurityPin).count()
    available_pins_count = db.query(SecurityPin).filter(SecurityPin.status.in_(['AVAILABLE', 'ISSUED'])).count()
    used_pins_count = db.query(SecurityPin).filter(SecurityPin.status == 'USED').count()
    expired_pins_count = db.query(SecurityPin).filter(SecurityPin.status == 'EXPIRED').count()
    
    pending_pin_orders_count = db.query(SecurityPinOrder).filter(SecurityPinOrder.status.in_(['PAYMENT_SUBMITTED', 'UNDER_REVIEW', 'PAYMENT_PENDING'])).count()
    completed_pin_orders_count = db.query(SecurityPinOrder).filter(SecurityPinOrder.status == 'COMPLETED').count()

    # Recent live feeds
    recent_users = db.query(User).filter(User.role != 'ADMIN').order_by(User.id.desc()).limit(6).all()
    recent_activations = db.query(Purchase).order_by(Purchase.id.desc()).limit(6).all()
    recent_transactions = db.query(WalletTransaction).order_by(WalletTransaction.id.desc()).limit(8).all()

    data = {
        'kpis': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'total_virtual_sales': total_sales,
            'total_packages_activated': total_packages_activated,
            'total_bv': total_bv,
            'total_left_bv': total_left_bv,
            'total_right_bv': total_right_bv,
            'total_left_carry': total_left_carry,
            'total_right_carry': total_right_carry,
            'total_matching_volume': total_matching_volume,
            'total_commissions': total_commissions,
            'direct_commissions': direct_comm,
            'matching_commissions': matching_comm,
            'pair_commissions': pair_comm,
            'carry_commissions': carry_comm,
            'total_wallet_balance': total_wallet_balance,
            'total_withdrawn': total_withdrawn,
            'pending_withdrawals_count': pending_count,
            'pending_withdrawals_amount': pending_amount,
            'approved_withdrawals_count': approved_withdrawals_count,
            'rejected_withdrawals_count': rejected_withdrawals_count,
            'pending_activations_count': pending_activations_count,
            'verified_activations_count': verified_activations_count,
            'total_pins_count': total_pins_count,
            'available_pins_count': available_pins_count,
            'used_pins_count': used_pins_count,
            'expired_pins_count': expired_pins_count,
            'issued_pins_count': available_pins_count,
            'total_activated_count': used_pins_count,
            'pending_pin_orders_count': pending_pin_orders_count,
            'completed_pin_orders_count': completed_pin_orders_count,
            'current_slot_id': slot_info.slot_id,
            'current_slot_name': slot_info.slot_name,
            'slot_virtual_sales': slot_purchases_sum,
            'slot_bv': slot_bv_sum,
            'slot_commissions': slot_commissions_sum,
            'slot_purchases_count': slot_purchases_count
        },
        'slot_info': slot_info.to_dict(),
        'recent_logs': [l.to_dict() for l in recent_logs],
        'recent_users': [u.to_dict() for u in recent_users],
        'recent_activations': [a.to_dict() for a in recent_activations],
        'recent_transactions': [t.to_dict() for t in recent_transactions]
    }
    return success_response(data)


@router.get("/users")
def admin_get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (User.user_code.ilike(s)) | (User.email.ilike(s)) | (User.mobile.ilike(s)))
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
        
    total = query.count()
    offset = (page - 1) * per_page
    users = query.order_by(User.id.asc()).offset(offset).limit(per_page).all()
    
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return success_response({
        'items': [u.to_dict() for u in users],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.post("/users/{user_id}/status")
def admin_toggle_user_status(
    user_id: int,
    req: UserStatusRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)
    if not user:
        return error_response("NOT_FOUND", "User not found.", 404)
        
    user.is_active = req.is_active
    db.commit()
    return success_response(user.to_dict(), f"User status set to {'Active' if user.is_active else 'Inactive'}.")

@router.post("/users/{user_id}/adjust-wallet")
def admin_adjust_wallet(
    user_id: int,
    req: WalletAdjustmentRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        txn = adjust_wallet_balance(
            db,
            user_id=user_id,
            amount=req.amount,
            admin_id=current_admin.id,
            reason=req.reason
        )
        db.commit()
        return success_response(txn.to_dict(), f"Wallet adjusted by ₹{req.amount:+,.2f} successfully.")
    except Exception as e:
        db.rollback()
        return error_response("ADJUSTMENT_FAILED", str(e), 400)

@router.get("/withdrawals")
def admin_get_withdrawals(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Withdrawal)
    if status_filter:
        query = query.filter(Withdrawal.status == status_filter.strip().upper())
        
    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(Withdrawal.created_at.desc()).offset(offset).limit(per_page).all()
    
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return success_response({
        'items': [w.to_dict() for w in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.post("/withdrawals/{withdrawal_id}/approve")
def admin_approve_withdrawal(
    withdrawal_id: int,
    req: Optional[AdminApprovalRequest] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        withdrawal = approve_withdrawal(
            db,
            withdrawal_id=withdrawal_id,
            admin_id=current_admin.id,
            notes=req.notes if req else None
        )
        db.commit()
        return success_response(withdrawal.to_dict(), f"Withdrawal request {withdrawal.withdrawal_code} approved.")
    except Exception as e:
        db.rollback()
        return error_response("APPROVAL_FAILED", str(e), 400)

@router.post("/withdrawals/{withdrawal_id}/reject")
def admin_reject_withdrawal(
    withdrawal_id: int,
    req: Optional[AdminApprovalRequest] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        withdrawal = reject_withdrawal(
            db,
            withdrawal_id=withdrawal_id,
            admin_id=current_admin.id,
            notes=req.notes if req else None
        )
        db.commit()
        return success_response(withdrawal.to_dict(), f"Withdrawal request {withdrawal.withdrawal_code} marked as rejected.")
    except Exception as e:
        db.rollback()
        return error_response("REJECTION_FAILED", str(e), 400)

from app.services.backup_service import backup_service
from app.services.integrity_service import integrity_service

@router.get("/system/database")
def admin_get_database_health(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Provides safe SQLite database health status, file size, table counts, and PRAGMA settings."""
    health = integrity_service.get_database_health(db)
    return success_response(health)

@router.get("/system/integrity")
def admin_run_integrity_check(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Runs structural, referential, and financial integrity audits on the persistent SQLite database."""
    audit_results = integrity_service.run_integrity_audit(db)
    return success_response(audit_results)

@router.post("/system/backup")
def admin_create_backup(
    payload: Optional[dict] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Creates a consistent, point-in-time SQLite online backup without interrupting live transactions."""
    notes = (payload or {}).get("notes", "Admin manual backup")
    try:
        res = backup_service.create_database_backup(current_admin.id, notes=notes)
        return success_response(res, "Database backup created successfully!")
    except Exception as e:
        return error_response("BACKUP_FAILED", str(e), 500)

@router.get("/system/backups")
def admin_list_backups(
    current_admin: User = Depends(get_current_admin)
):
    """Lists all available persistent SQLite database backups."""
    backups = backup_service.list_backups()
    return success_response(backups)

@router.post("/demo/reset")
def admin_reset_demo(
    payload: Optional[dict] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin reset endpoint. Strictly disabled in production environment."""
    if settings.is_production:
        return error_response("RESET_FORBIDDEN", "Database wipe is permanently disabled in PRODUCTION environment.", 403)
    confirm_text = (payload or {}).get("confirm_text", "")
    try:
        reset_demo_database(db, confirm_text=confirm_text)
        return success_response(None, "Environment successfully reset to initial seed state!")
    except PermissionError as pe:
        return error_response("RESET_FORBIDDEN", str(pe), 403)
    except Exception as e:
        db.rollback()
        return error_response("RESET_FAILED", str(e), 500)

# ==========================================
# TIME CONTROL & SLOT CONFIGURATION
# ==========================================

def _parse_custom_datetime(dt_str: str) -> datetime:
    dt_str = dt_str.strip()
    try:
        return datetime.fromisoformat(dt_str.replace(' ', 'T'))
    except Exception:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M"
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                pass
    raise ValueError(f"Invalid datetime format: '{dt_str}'. Supported formats: YYYY-MM-DD HH:MM or ISO 8601.")

@router.get("/time")
def admin_get_time_state(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    slot_info = time_provider.get_current_slot_info(db)
    return success_response(slot_info.to_dict())

@router.post("/time/mode")
def admin_set_time_mode(
    req: TimeModeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if settings.is_production:
        return error_response("FORBIDDEN", "Time simulation is disabled in PRODUCTION environment. Server IST clock is authoritative.", 403)
    mode = req.mode.strip().upper()
    if mode not in ('REAL', 'DEMO'):
        return error_response("INVALID_MODE", "Mode must be either 'REAL' or 'DEMO'.", 400)
        
    if mode == 'REAL':
        slot_info = time_provider.reset_to_real_time(db, current_admin.id)
        msg = "Time mode switched to LIVE REAL IST."
    else:
        # Default demo time to current time if entering DEMO mode
        curr_dt = time_provider.get_current_ist_time(db)
        slot_info = time_provider.set_demo_time(db, curr_dt, current_admin.id)
        msg = "Time mode switched to VIRTUAL TIME."

    return success_response(slot_info.to_dict(), msg)

@router.post("/time/set")
def admin_set_exact_time(
    req: SetTimeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if settings.is_production:
        return error_response("FORBIDDEN", "Time simulation is disabled in PRODUCTION environment. Server IST clock is authoritative.", 403)
    try:
        parsed_dt = _parse_custom_datetime(req.datetime)
        slot_info = time_provider.set_demo_time(db, parsed_dt, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Time set to {slot_info.date_str} {slot_info.time_formatted} ({slot_info.slot_name})."
        )
    except Exception as e:
        return error_response("SET_TIME_FAILED", str(e), 400)

@router.post("/time/advance")
def admin_advance_time(
    req: AdvanceTimeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if settings.is_production:
        return error_response("FORBIDDEN", "Time simulation is disabled in PRODUCTION environment. Server IST clock is authoritative.", 403)
    try:
        slot_info = time_provider.advance_demo_time(db, req.minutes, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Clock advanced by {req.minutes} min -> {slot_info.time_formatted} ({slot_info.slot_name})."
        )
    except Exception as e:
        return error_response("ADVANCE_TIME_FAILED", str(e), 400)

@router.post("/time/next-slot")
def admin_jump_next_slot(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if settings.is_production:
        return error_response("FORBIDDEN", "Time simulation is disabled in PRODUCTION environment. Server IST clock is authoritative.", 403)
    try:
        slot_info = time_provider.next_slot(db, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Jumped to beginning of {slot_info.slot_name} ({slot_info.slot_id}) at {slot_info.time_formatted}."
        )
    except Exception as e:
        return error_response("NEXT_SLOT_FAILED", str(e), 400)

@router.post("/time/previous-slot")
def admin_jump_previous_slot(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if settings.is_production:
        return error_response("FORBIDDEN", "Time simulation is disabled in PRODUCTION environment. Server IST clock is authoritative.", 403)
    try:
        slot_info = time_provider.previous_slot(db, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Jumped to beginning of {slot_info.slot_name} ({slot_info.slot_id}) at {slot_info.time_formatted}."
        )
    except Exception as e:
        return error_response("PREVIOUS_SLOT_FAILED", str(e), 400)

@router.post("/time/reset")
def admin_reset_time_to_real(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        slot_info = time_provider.reset_to_real_time(db, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            "System clock reset to authoritative India Standard Time."
        )
    except Exception as e:
        return error_response("RESET_TIME_FAILED", str(e), 400)

# ==========================================
# SETTLEMENT & VOLUME LEDGER AUDIT ENDPOINTS
# ==========================================

@router.get("/settlements")
def admin_get_settlements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    slot_id: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(SlotSettlement)
    if slot_id:
        query = query.filter(SlotSettlement.slot_id == slot_id.strip())
    if user_id:
        query = query.filter(SlotSettlement.user_id == user_id)
    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, SlotSettlement.user_id == User.id)\
            .filter((User.full_name.ilike(s)) | (User.user_code.ilike(s)))

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SlotSettlement.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [s.to_dict() for s in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.get("/volume-ledger")
def admin_get_volume_ledger(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    slot_id: Optional[str] = Query(None),
    ancestor_user_id: Optional[int] = Query(None),
    source_user_id: Optional[int] = Query(None),
    side: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(VolumeLedger)
    if slot_id:
        query = query.filter(VolumeLedger.slot_id == slot_id.strip())
    if ancestor_user_id:
        query = query.filter(VolumeLedger.ancestor_user_id == ancestor_user_id)
    if source_user_id:
        query = query.filter(VolumeLedger.source_user_id == source_user_id)
    if side:
        query = query.filter(VolumeLedger.side == side.strip().upper())
    if status:
        query = query.filter(VolumeLedger.status == status.strip().upper())

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(VolumeLedger.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [v.to_dict() for v in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.get("/commissions")
def admin_get_commissions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    slot_id: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    source_user_id: Optional[int] = Query(None),
    comm_type: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Commission)
    if slot_id:
        query = query.filter(Commission.slot_id == slot_id.strip())
    if user_id:
        query = query.filter(Commission.beneficiary_id == user_id)
    if source_user_id:
        query = query.filter(Commission.source_user_id == source_user_id)
    if comm_type:
        ctype = comm_type.strip()
        if ctype in ('DIRECT_REFERRAL', 'DIRECT_COMMISSION'):
            query = query.filter(Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION']))
        elif ctype in ('MATCHING_COMMISSION', 'BINARY_MATCHING'):
            query = query.filter(Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING']))
        else:
            query = query.filter(Commission.commission_type == ctype)
    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, Commission.beneficiary_id == User.id)\
            .filter((User.full_name.ilike(s)) | (User.user_code.ilike(s)))

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(Commission.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [c.to_dict() for c in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

# ----------------------------------------------------
# Security PIN & Package Activation Management Endpoints
# ----------------------------------------------------

@router.get("/activation-requests")
def admin_get_activation_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(PackageActivationRequest)

    if status_filter:
        sf = status_filter.strip().upper()
        if sf != 'ALL':
            query = query.filter(PackageActivationRequest.status == sf)

    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, PackageActivationRequest.user_id == User.id)\
            .filter(
                (User.full_name.ilike(s)) |
                (User.user_code.ilike(s)) |
                (User.email.ilike(s)) |
                (PackageActivationRequest.request_code.ilike(s)) |
                (PackageActivationRequest.payment_reference.ilike(s))
            )

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(PackageActivationRequest.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [req.to_dict() for req in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.get("/activation-requests/{request_id}")
def admin_get_activation_request_detail(
    request_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    req = db.get(PackageActivationRequest, request_id)
    if not req:
        return error_response("NOT_FOUND", "Activation request not found.", 404)

    return success_response(req.to_dict())

@router.post("/activation-requests/{request_id}/verify-payment")
def admin_verify_activation_payment(
    request_id: int,
    req_body: Optional[AdminVerifyPaymentRequest] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        notes = req_body.admin_notes if req_body else None
        req = pin_service.verify_payment(
            db=db,
            request_id=request_id,
            admin_id=current_admin.id,
            admin_notes=notes
        )
        db.commit()
        return success_response(
            req.to_dict(),
            f"Payment for request {req.request_code} verified! You may now issue a Security PIN."
        )
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("VERIFICATION_FAILED", str(e), 400)

@router.post("/activation-requests/{request_id}/issue-pin")
def admin_issue_pin_for_request(
    request_id: int,
    req_body: Optional[AdminIssuePinRequest] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        expires_in = req_body.expires_in_days if req_body and req_body.expires_in_days else 7
        pin, raw_pin = pin_service.issue_security_pin(
            db=db,
            request_id=request_id,
            admin_id=current_admin.id,
            expires_in_days=expires_in
        )
        db.commit()

        # Plaintext PIN is returned strictly ONCE in this response for admin to provide to user
        pin_data = pin.to_dict(include_pin_code=True)
        pin_data['raw_security_pin'] = raw_pin

        req = db.get(PackageActivationRequest, request_id)

        return success_response({
            'pin': pin_data,
            'activation_request': req.to_dict() if req else None,
            'raw_security_pin': raw_pin
        }, f"Security PIN generated successfully. Please copy and provide this PIN to the user.")
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("PIN_ISSUANCE_FAILED", str(e), 400)

@router.post("/activation-requests/{request_id}/reject")
def admin_reject_activation_request(
    request_id: int,
    req_body: AdminRejectRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        req = pin_service.reject_request(
            db=db,
            request_id=request_id,
            admin_id=current_admin.id,
            reason=req_body.reason
        )
        db.commit()
        return success_response(req.to_dict(), f"Activation request {req.request_code} rejected.")
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("REJECTION_FAILED", str(e), 400)

@router.post("/security-pins/{pin_id}/revoke")
def admin_revoke_security_pin(
    pin_id: int,
    req_body: AdminRevokePinRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        pin = pin_service.revoke_pin(
            db=db,
            pin_id=pin_id,
            admin_id=current_admin.id,
            reason=req_body.reason
        )
        db.commit()
        return success_response(pin.to_dict(include_pin_code=True), f"Security PIN {pin.pin_code} revoked.")
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("REVOCATION_FAILED", str(e), 400)

@router.get("/security-pins")
def admin_get_security_pins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(SecurityPin)
    if status_filter and status_filter.strip().upper() != 'ALL':
        query = query.filter(SecurityPin.status == status_filter.strip().upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, SecurityPin.user_id == User.id)\
            .filter((User.full_name.ilike(s)) | (User.user_code.ilike(s)) | (SecurityPin.pin_code.ilike(s)))

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SecurityPin.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [p.to_dict(include_pin_code=True) for p in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

# =========================================================================
# PREPAID BULK PIN ORDERS & INVENTORY MANAGEMENT
# =========================================================================

@router.get("/pin-orders")
@router.get("/security-pins/orders")
def admin_get_pin_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from app.models.pin_order import SecurityPinOrder
    query = db.query(SecurityPinOrder)
    if status_filter and status_filter.strip().upper() != 'ALL':
        query = query.filter(SecurityPinOrder.status == status_filter.strip().upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.join(User, SecurityPinOrder.user_id == User.id)\
            .filter((User.full_name.ilike(s)) | (User.user_code.ilike(s)) | (SecurityPinOrder.order_code.ilike(s)) | (SecurityPinOrder.payment_reference.ilike(s)))

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SecurityPinOrder.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [o.to_dict() for o in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.post("/pin-orders/{order_id}/verify")
@router.post("/security-pins/orders/{order_id}/verify")
def admin_verify_pin_order_payment(
    order_id: int,
    req_body: AdminVerifyPaymentRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        order = pin_service.admin_verify_order_payment(
            db=db,
            order_id=order_id,
            admin_id=current_admin.id,
            admin_notes=req_body.admin_notes
        )
        db.commit()
        return success_response(order.to_dict(), f"Payment for PIN Order {order.order_code} verified successfully.")
    except Exception as e:
        db.rollback()
        return error_response("VERIFICATION_FAILED", str(e), 400)

@router.post("/pin-orders/{order_id}/issue")
@router.post("/security-pins/orders/{order_id}/issue")
def admin_issue_pin_order_batch(
    order_id: int,
    req_body: AdminIssuePinRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        expires_in = req_body.expires_in_days or 30
        order, generated_pins = pin_service.admin_issue_pin_batch(
            db=db,
            order_id=order_id,
            admin_id=current_admin.id,
            expires_in_days=expires_in
        )
        db.commit()
        return success_response({
            'order': order.to_dict(),
            'generated_pins': generated_pins,
            'pins': generated_pins,
            'raw_security_pins': [p.get('raw_pin') for p in generated_pins],
            'count': len(generated_pins)
        }, f"Successfully generated and credited {len(generated_pins)} Security PIN(s) to buyer's wallet.")
    except Exception as e:
        db.rollback()
        return error_response("PIN_ISSUANCE_FAILED", str(e), 400)

@router.post("/pin-orders/{order_id}/reject")
@router.post("/security-pins/orders/{order_id}/reject")
def admin_reject_pin_order(
    order_id: int,
    req_body: AdminRejectRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        order = pin_service.admin_reject_order(
            db=db,
            order_id=order_id,
            admin_id=current_admin.id,
            rejection_reason=req_body.reason
        )
        db.commit()
        return success_response(order.to_dict(), f"PIN Order {order.order_code} rejected.")
    except Exception as e:
        db.rollback()
        return error_response("REJECTION_FAILED", str(e), 400)

@router.get("/pin-transfers")
@router.get("/security-pins/transfers")
def admin_get_pin_transfers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from app.models.pin_transfer import SecurityPinTransfer
    query = db.query(SecurityPinTransfer)
    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SecurityPinTransfer.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [t.to_dict() for t in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.get("/pin-ledger")
@router.get("/security-pins/ledger")
def admin_get_pin_ledger(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from app.models.pin_ledger import SecurityPinLedger
    query = db.query(SecurityPinLedger)
    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SecurityPinLedger.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [l.to_dict() for l in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })



