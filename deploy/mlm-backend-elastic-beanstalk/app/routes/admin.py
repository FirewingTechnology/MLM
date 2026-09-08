from flask import Blueprint, request
from app.extensions import db
from app.models.user import User
from app.models.purchase import Purchase
from app.models.commission import Commission
from app.models.withdrawal import Withdrawal
from app.models.wallet import Wallet, WalletTransaction
from app.models.volume import BinaryVolume
from app.models.audit_log import AuditLog
from app.services.wallet_service import approve_withdrawal, reject_withdrawal, adjust_wallet
from app.services.seed_service import reset_demo_database
from app.services.audit_service import log_action
from app.utils.responses import success_response, error_response
from app.middleware.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard(current_admin):
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    total_sales = db.session.query(db.func.sum(Purchase.amount)).scalar() or 0.0
    total_bv = db.session.query(db.func.sum(Purchase.bv)).scalar() or 0.0
    
    total_commissions = db.session.query(db.func.sum(Commission.amount)).scalar() or 0.0
    direct_commissions = db.session.query(db.func.sum(Commission.amount)).filter(Commission.commission_type == 'DIRECT_REFERRAL').scalar() or 0.0
    matching_commissions = db.session.query(db.func.sum(Commission.amount)).filter(Commission.commission_type == 'BINARY_MATCHING').scalar() or 0.0
    
    total_withdrawn = db.session.query(db.func.sum(Withdrawal.amount)).filter(Withdrawal.status == 'APPROVED').scalar() or 0.0
    pending_withdrawals_count = Withdrawal.query.filter_by(status='PENDING').count()
    pending_withdrawals_amount = db.session.query(db.func.sum(Withdrawal.amount)).filter(Withdrawal.status == 'PENDING').scalar() or 0.0

    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    recent_purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(6).all()

    return success_response({
        'kpis': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_virtual_sales': total_sales,
            'total_bv': total_bv,
            'total_commissions': total_commissions,
            'direct_commissions': direct_commissions,
            'matching_commissions': matching_commissions,
            'total_withdrawn': total_withdrawn,
            'pending_withdrawals_count': pending_withdrawals_count,
            'pending_withdrawals_amount': pending_withdrawals_amount
        },
        'recent_logs': [l.to_dict() for l in recent_logs],
        'recent_purchases': [p.to_dict() for p in recent_purchases]
    })

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_admin):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = User.query
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") |
            User.user_code.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%") |
            User.mobile.ilike(f"%{search}%") |
            User.referral_code.ilike(f"%{search}%")
        )
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    pagination = query.order_by(User.id.asc()).paginate(page=page, per_page=per_page, error_out=False)

    users_data = []
    for u in pagination.items:
        vol = u.volume
        wal = u.wallet
        users_data.append({
            **u.to_dict(),
            'wallet_balance': wal.balance if wal else 0,
            'total_earned': wal.total_earned if wal else 0,
            'total_withdrawn': wal.total_withdrawn if wal else 0,
            'personal_bv': vol.personal_bv if vol else 0,
            'left_bv': vol.accumulated_left_bv if vol else 0,
            'right_bv': vol.accumulated_right_bv if vol else 0,
            'carry_left_bv': vol.carry_left_bv if vol else 0,
            'carry_right_bv': vol.carry_right_bv if vol else 0,
            'matched_bv': vol.matched_bv if vol else 0,
            'direct_referrals_count': User.query.filter_by(sponsor_id=u.id).count()
        })

    return success_response({
        'items': users_data,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(current_admin, user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error_response("NOT_FOUND", "User not found.", 404)

    vol = user.volume
    wal = user.wallet
    direct_users = User.query.filter_by(sponsor_id=user.id).all()
    user_purchases = user.purchases.order_by(Purchase.created_at.desc()).all()
    user_commissions = Commission.query.filter_by(beneficiary_id=user.id).order_by(Commission.created_at.desc()).limit(10).all()
    user_txns = WalletTransaction.query.filter_by(user_id=user.id).order_by(WalletTransaction.created_at.desc()).limit(10).all()

    return success_response({
        'user': user.to_dict(),
        'wallet': wal.to_dict() if wal else None,
        'volume': vol.to_dict() if vol else None,
        'direct_referrals': [d.to_dict() for d in direct_users],
        'purchases': [p.to_dict() for p in user_purchases],
        'recent_commissions': [c.to_dict() for c in user_commissions],
        'recent_transactions': [t.to_dict() for t in user_txns]
    })

@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@admin_required
def toggle_user_status(current_admin, user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error_response("NOT_FOUND", "User not found.", 404)

    data = request.get_json() or {}
    is_active = data.get('is_active', not user.is_active)
    user.is_active = is_active
    
    log_action('ADMIN_USER_STATUS_CHANGE', 'User', user.user_code, current_admin.id, {'new_status': is_active})
    db.session.commit()
    
    return success_response(user.to_dict(), f"User status updated to {'Active' if is_active else 'Inactive'}.")

@admin_bp.route('/users/<int:user_id>/adjust-wallet', methods=['POST'])
@admin_required
def admin_adjust_wallet(current_admin, user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error_response("NOT_FOUND", "User not found.", 404)

    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return error_response("INVALID_AMOUNT", "Valid numerical amount required.")
        
    reason = data.get('reason', '').strip()
    if not reason:
        return error_response("VALIDATION_ERROR", "A reason is mandatory for admin adjustments.")

    try:
        txn = adjust_wallet(user_id=user.id, amount=amount, reason=reason, admin_id=current_admin.id)
        db.session.commit()
        return success_response(txn.to_dict(), f"Wallet adjusted by ₹{amount:+,.2f} successfully.")
    except Exception as e:
        db.session.rollback()
        return error_response("ADJUSTMENT_FAILED", str(e), 400)

@admin_bp.route('/withdrawals', methods=['GET'])
@admin_required
def get_all_withdrawals(current_admin):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '').strip()

    query = Withdrawal.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Withdrawal.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [w.to_dict() for w in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })

@admin_bp.route('/withdrawals/<int:withdrawal_id>/approve', methods=['POST'])
@admin_required
def admin_approve_withdrawal(current_admin, withdrawal_id):
    data = request.get_json() or {}
    notes = data.get('notes', 'Approved by Admin')

    try:
        withdrawal = approve_withdrawal(withdrawal_id, current_admin.id, notes)
        db.session.commit()
        return success_response(withdrawal.to_dict(), f"Withdrawal request #{withdrawal.withdrawal_code} approved.")
    except Exception as e:
        db.session.rollback()
        return error_response("APPROVAL_FAILED", str(e), 400)

@admin_bp.route('/withdrawals/<int:withdrawal_id>/reject', methods=['POST'])
@admin_required
def admin_reject_withdrawal(current_admin, withdrawal_id):
    data = request.get_json() or {}
    notes = data.get('notes', 'Rejected by Admin')

    try:
        withdrawal = reject_withdrawal(withdrawal_id, current_admin.id, notes)
        db.session.commit()
        return success_response(withdrawal.to_dict(), f"Withdrawal request #{withdrawal.withdrawal_code} rejected.")
    except Exception as e:
        db.session.rollback()
        return error_response("REJECTION_FAILED", str(e), 400)

@admin_bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs(current_admin):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })

@admin_bp.route('/demo/reset', methods=['POST'])
@admin_required
def reset_demo(current_admin):
    try:
        reset_demo_database()
        return success_response(None, "Demo environment successfully reset to initial seed state!")
    except Exception as e:
        db.session.rollback()
        return error_response("RESET_FAILED", f"Failed to reset demo: {str(e)}", 500)
