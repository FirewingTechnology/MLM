from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.commission import Commission
from app.models.wallet import Wallet
from app.models.withdrawal import Withdrawal
from app.models.audit_log import AuditLog
from app.schemas.common import AdminApprovalRequest, WalletAdjustmentRequest, UserStatusRequest
from app.security import get_current_admin
from app.services.wallet_service import approve_withdrawal, reject_withdrawal, adjust_wallet_balance
from app.services.seed_service import reset_demo_database
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
        .filter(Commission.commission_type == 'DIRECT_REFERRAL').scalar() or 0.0
    matching_comm = db.query(func.coalesce(func.sum(Commission.amount), 0.0))\
        .filter(Commission.commission_type == 'BINARY_MATCHING').scalar() or 0.0
        
    total_withdrawn = db.query(func.coalesce(func.sum(Wallet.total_withdrawn), 0.0)).scalar() or 0.0
    
    pending_withdrawals_query = db.query(Withdrawal).filter(Withdrawal.status == 'PENDING')
    pending_count = pending_withdrawals_query.count()
    pending_amount = db.query(func.coalesce(func.sum(Withdrawal.amount), 0.0))\
        .filter(Withdrawal.status == 'PENDING').scalar() or 0.0
        
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
    
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
            'total_withdrawn': total_withdrawn,
            'pending_withdrawals_count': pending_count,
            'pending_withdrawals_amount': pending_amount
        },
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
