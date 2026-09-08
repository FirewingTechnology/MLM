from flask import Blueprint, request
from app.models.wallet import WalletTransaction
from app.services.wallet_service import get_or_create_wallet
from app.utils.responses import success_response
from app.middleware.auth import token_required

wallet_bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')

@wallet_bp.route('', methods=['GET'])
@token_required
def get_wallet_overview(current_user):
    wallet = get_or_create_wallet(current_user.id)
    return success_response(wallet.to_dict())

@wallet_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '').strip()
    txn_type = request.args.get('type', '').strip()

    query = WalletTransaction.query.filter_by(user_id=current_user.id)
    
    if category:
        query = query.filter_by(category=category)
    if txn_type:
        query = query.filter_by(type=txn_type)

    pagination = query.order_by(WalletTransaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })
