from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.commission import Commission
from app.security import get_current_user
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/commissions", tags=["commissions"])

@router.get("")
def get_commissions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    comm_type: Optional[str] = Query(None, alias="type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Commission).filter(Commission.beneficiary_id == current_user.id)
    if comm_type:
        ctype = comm_type.strip()
        if ctype in ('DIRECT_REFERRAL', 'DIRECT_COMMISSION'):
            query = query.filter(Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION']))
        elif ctype in ('MATCHING_COMMISSION', 'BINARY_MATCHING'):
            query = query.filter(Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING']))
        else:
            query = query.filter(Commission.commission_type == ctype)

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(Commission.created_at.desc()).offset(offset).limit(per_page).all()
    
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    direct_all = db.query(Commission).filter(
        Commission.beneficiary_id == current_user.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).all()
    matching_all = db.query(Commission).filter(
        Commission.beneficiary_id == current_user.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).all()
    pair_all = db.query(Commission).filter(
        Commission.beneficiary_id == current_user.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).all()
    carry_all = db.query(Commission).filter(
        Commission.beneficiary_id == current_user.id,
        Commission.commission_type == 'CARRY_COMMISSION'
    ).all()

    return success_response({
        'items': [c.to_dict() for c in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'total_direct_amount': sum(c.amount for c in direct_all),
        'total_pair_amount': sum(c.amount for c in pair_all),
        'total_matching_amount': sum(c.amount for c in matching_all),
        'total_carry_amount': sum(c.amount for c in carry_all)
    })

@router.get("/{commission_id}")
def get_commission_detail(
    commission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    commission = db.get(Commission, commission_id)
    if not commission:
        return error_response("NOT_FOUND", "Commission record not found.", 404)
        
    if current_user.role != 'ADMIN' and commission.beneficiary_id != current_user.id:
        return error_response("FORBIDDEN", "Unauthorized to view this commission details.", 403)

    return success_response(commission.to_dict())
