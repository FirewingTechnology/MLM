from flask import Blueprint, request
from app.models.purchase import Purchase
from app.services.commission_service import process_package_purchase
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

purchases_bp = Blueprint('purchases', __name__, url_prefix='/api/purchases')

@purchases_bp.route('', methods=['POST'])
@token_required
def buy_package(current_user):
    data = request.get_json() or {}
    package_id = data.get('package_id', None)
    idempotency_key = data.get('idempotency_key', None)

    try:
        purchase, events = process_package_purchase(
            user_id=current_user.id,
            package_id=package_id,
            idempotency_key=idempotency_key
        )
        return success_response({
            'purchase': purchase.to_dict(),
            'events': events,
            'user': current_user.to_dict(),
            'wallet': current_user.wallet.to_dict() if current_user.wallet else None,
            'volume': current_user.volume.to_dict() if current_user.volume else None
        }, f"Virtual package purchase of ₹{purchase.amount:,.0f} completed! +{purchase.bv:,.0f} BV Added.", 201)
    except Exception as e:
        return error_response("PURCHASE_FAILED", str(e), 400)

@purchases_bp.route('/my', methods=['GET'])
@token_required
def my_purchases(current_user):
    purchases = current_user.purchases.order_by(Purchase.created_at.desc()).all()
    return success_response([p.to_dict() for p in purchases])
