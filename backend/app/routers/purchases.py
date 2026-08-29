from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase
from app.schemas.common import PurchaseRequest
from app.security import get_current_user
from app.services.commission_service import process_package_purchase
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/purchases", tags=["purchases"])

@router.post("", status_code=201)
def buy_package(
    req: PurchaseRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    package_id = req.package_id if req else None
    idempotency_key = req.idempotency_key if req else None

    try:
        purchase, events = process_package_purchase(
            db,
            user_id=current_user.id,
            package_id=package_id,
            idempotency_key=idempotency_key
        )
        db.commit()
        return success_response({
            'purchase': purchase.to_dict(),
            'events': events,
            'user': current_user.to_dict(),
            'wallet': current_user.wallet.to_dict() if current_user.wallet else None,
            'volume': current_user.volume.to_dict() if current_user.volume else None
        }, f"Package purchase of ₹{purchase.amount:,.0f} completed! +{purchase.bv:,.0f} BV Added.", 201)
    except Exception as e:
        db.rollback()
        return error_response("PURCHASE_FAILED", str(e), 400)

@router.get("/my")
def my_purchases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    purchases = db.query(Purchase).filter(Purchase.user_id == current_user.id).order_by(Purchase.created_at.desc()).all()
    return success_response([p.to_dict() for p in purchases])
