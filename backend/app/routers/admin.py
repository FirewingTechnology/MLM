from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
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
from app.schemas.common import AdminApprovalRequest, WalletAdjustmentRequest, UserStatusRequest
from app.schemas.time_schemas import TimeModeRequest, SetTimeRequest, AdvanceTimeRequest
from app.security import get_current_admin
from app.services.wallet_service import approve_withdrawal, reject_withdrawal, adjust_wallet_balance
from app.services.seed_service import reset_demo_database
from app.services.time_service import time_provider, slot_service
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
    total_bv = db.query(func.coalesce(func.sum(BinaryVolume.personal_bv), 0.0)).scalar() or 0.0
    
    total_commissions = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).scalar() or 0.0
    direct_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])).scalar() or 0.0
    matching_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])).scalar() or 0.0
    pair_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type == 'PAIR_BONUS').scalar() or 0.0
    carry_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type == 'CARRY_COMMISSION').scalar() or 0.0
        
    total_withdrawn = db.query(func.coalesce(func.sum(Wallet.total_withdrawn), 0.0)).scalar() or 0.0
    
    pending_withdrawals_query = db.query(Withdrawal).filter(Withdrawal.status == 'PENDING')
    pending_count = pending_withdrawals_query.count()
    pending_amount = db.query(func.coalesce(func.sum(Withdrawal.amount), 0.0))\
        .filter(Withdrawal.status == 'PENDING').scalar() or 0.0
        
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

    data = {
        'kpis': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'total_virtual_sales': total_sales,
            'total_bv': total_bv,
            'total_commissions': total_commissions,
            'direct_commissions': direct_comm,
            'matching_commissions': matching_comm,
            'pair_commissions': pair_comm,
            'carry_commissions': carry_comm,
            'total_withdrawn': total_withdrawn,
            'pending_withdrawals_count': pending_count,
            'pending_withdrawals_amount': pending_amount,
            'current_slot_id': slot_info.slot_id,
            'current_slot_name': slot_info.slot_name,
            'slot_virtual_sales': slot_purchases_sum,
            'slot_bv': slot_bv_sum,
            'slot_commissions': slot_commissions_sum,
            'slot_purchases_count': slot_purchases_count
        },
        'slot_info': slot_info.to_dict(),
        'recent_logs': [l.to_dict() for l in recent_logs]
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

@router.post("/demo/reset")
def admin_reset_demo(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        reset_demo_database(db)
        return success_response(None, "Demo environment successfully reset to initial seed state!")
    except Exception as e:
        db.rollback()
        return error_response("RESET_FAILED", str(e), 500)

# ==========================================
# DEMO TIME CONTROL ENDPOINTS
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
        msg = "Time mode switched to VIRTUAL DEMO TIME."

    return success_response(slot_info.to_dict(), msg)

@router.post("/time/set")
def admin_set_exact_time(
    req: SetTimeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        parsed_dt = _parse_custom_datetime(req.datetime)
        slot_info = time_provider.set_demo_time(db, parsed_dt, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Demo time set to {slot_info.date_str} {slot_info.time_formatted} ({slot_info.slot_name})."
        )
    except Exception as e:
        return error_response("SET_TIME_FAILED", str(e), 400)

@router.post("/time/advance")
def admin_advance_time(
    req: AdvanceTimeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        slot_info = time_provider.advance_demo_time(db, req.minutes, current_admin.id)
        return success_response(
            slot_info.to_dict(),
            f"Demo clock advanced by {req.minutes} min -> {slot_info.time_formatted} ({slot_info.slot_name})."
        )
    except Exception as e:
        return error_response("ADVANCE_TIME_FAILED", str(e), 400)

@router.post("/time/next-slot")
def admin_jump_next_slot(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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
            "Demo time reset. System is now running on LIVE INDIA STANDARD TIME."
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

