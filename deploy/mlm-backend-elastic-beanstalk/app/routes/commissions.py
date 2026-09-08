from flask import Blueprint, request
from app.extensions import db
from app.models.commission import Commission
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

commissions_bp = Blueprint('commissions', __name__, url_prefix='/api/commissions')

@commissions_bp.route('', methods=['GET'])
@token_required
def get_commissions(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    comm_type = request.args.get('type', '').strip()

    query = Commission.query.filter_by(beneficiary_id=current_user.id)
    if comm_type:
        query = query.filter_by(commission_type=comm_type)

    pagination = query.order_by(Commission.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'total_direct_amount': sum(c.amount for c in Commission.query.filter_by(beneficiary_id=current_user.id, commission_type='DIRECT_REFERRAL').all()),
        'total_matching_amount': sum(c.amount for c in Commission.query.filter_by(beneficiary_id=current_user.id, commission_type='BINARY_MATCHING').all())
    })

@commissions_bp.route('/<int:commission_id>', methods=['GET'])
@token_required
def get_commission_detail(current_user, commission_id):
    commission = db.session.get(Commission, commission_id)
    if not commission:
        return error_response("NOT_FOUND", "Commission record not found.", 404)
        
    if current_user.role != 'ADMIN' and commission.beneficiary_id != current_user.id:
        return error_response("FORBIDDEN", "Unauthorized to view this commission details.", 403)

    return success_response(commission.to_dict())
