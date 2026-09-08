from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.withdrawal import Withdrawal
from app.schemas.common import WithdrawalRequest
from app.security import get_current_user
from app.services.wallet_service import create_withdrawal_request
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/withdrawals", tags=["withdrawals"])

@router.post("", status_code=201)
def request_withdrawal(
    req: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        withdrawal = create_withdrawal_request(
            db,
            user_id=current_user.id,
            amount=req.amount,
            payout_method=req.payout_method or 'VIRTUAL_UPI',
            payout_details=req.payout_details
        )
        db.commit()
        return success_response(
            withdrawal.to_dict(),
            f"Demo withdrawal request for ₹{withdrawal.amount:,.2f} submitted for admin approval.",
            201
        )
    except Exception as e:
        db.rollback()
        return error_response("WITHDRAWAL_FAILED", str(e), 400)

@router.get("")
def my_withdrawals(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Withdrawal).filter(Withdrawal.user_id == current_user.id)
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
