from flask import Blueprint, request
from app.extensions import db
from app.models.withdrawal import Withdrawal
from app.services.wallet_service import create_withdrawal_request
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

withdrawals_bp = Blueprint('withdrawals', __name__, url_prefix='/api/withdrawals')

@withdrawals_bp.route('', methods=['POST'])
@token_required
def request_withdrawal(current_user):
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return error_response("INVALID_AMOUNT", "Please enter a valid numeric withdrawal amount.")

    payout_method = data.get('payout_method', 'VIRTUAL_UPI')
    payout_details = data.get('payout_details', {})

    try:
        withdrawal = create_withdrawal_request(
            user_id=current_user.id,
            amount=amount,
            payout_method=payout_method,
            payout_details=payout_details
        )
        db.session.commit()
        return success_response(
            withdrawal.to_dict(),
            f"Virtual withdrawal request for ₹{amount:,.2f} submitted successfully (Status: PENDING).",
            201
        )
    except Exception as e:
        db.session.rollback()
        return error_response("WITHDRAWAL_FAILED", str(e), 400)

@withdrawals_bp.route('', methods=['GET'])
@token_required
def get_my_withdrawals(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = current_user.withdrawals.order_by(Withdrawal.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [w.to_dict() for w in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })
