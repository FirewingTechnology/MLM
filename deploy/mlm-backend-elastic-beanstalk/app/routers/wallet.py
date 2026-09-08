from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.security import get_current_user
from app.services.wallet_service import get_or_create_wallet
from app.utils.responses import success_response

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

@router.get("")
def get_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wallet = get_or_create_wallet(db, current_user.id)
    return success_response(wallet.to_dict())

@router.get("/transactions")
def get_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    txn_type: Optional[str] = Query(None, alias="type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id)
    if txn_type:
        query = query.filter(WalletTransaction.transaction_type == txn_type.strip().upper())
        
    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(per_page).all()
    
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return success_response({
        'items': [t.to_dict() for t in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })
