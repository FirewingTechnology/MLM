from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.user import User
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_upline_request import SecurityPinUplineRequest
from app.models.pin_ledger import SecurityPinLedger
from app.services.pin_service import pin_service, PinValidationError, PinSecurityError
from app.security import get_current_user
from app.schemas.security_pins import (
    PinOrderCreateRequest,
    PinTransferRequest,
    PinUplineRequestCreate,
    PinUplineRequestRespond,
    PinUseRequest
)

router = APIRouter(prefix="/api/security-pins", tags=["Security PIN Inventory & Wallet"])

# =========================================================================
# 1. USER PIN INVENTORY & WALLET
# =========================================================================

@router.get("/inventory")
def get_pin_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the user's PIN wallet balance, summary counts, and available PINs."""
    try:
        data = pin_service.get_user_pin_inventory(db, current_user.id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/downline-eligible")
def get_downline_eligible_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns list of eligible downline network members for PIN distribution."""
    try:
        users = pin_service.get_eligible_downlines(db, current_user.id)
        return {"success": True, "data": users}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# =========================================================================
# 2. BULK PIN PURCHASE ORDERS (FROM ADMIN)
# =========================================================================

@router.post("/orders")
def create_pin_order(
    payload: PinOrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User submits a bulk PIN purchase request with payment reference to Admin."""
    try:
        order = pin_service.create_pin_order(
            db=db,
            user_id=current_user.id,
            package_id=payload.package_id,
            quantity=payload.quantity,
            payment_method=payload.payment_method,
            payment_reference=payload.payment_reference,
            payment_proof_url=payload.payment_proof_url,
            amount=payload.amount
        )
        db.commit()
        db.refresh(order)
        return {
            "success": True,
            "message": f"Successfully created PIN order for {order.quantity} PIN(s) (₹{order.total_amount:,.2f}). Waiting for Admin verification.",
            "data": order.to_dict()
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/orders")
def list_user_pin_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns all PIN purchase orders submitted by the current user."""
    orders = db.query(SecurityPinOrder).filter(
        SecurityPinOrder.user_id == current_user.id
    ).order_by(SecurityPinOrder.id.desc()).all()
    return {"success": True, "data": [o.to_dict() for o in orders]}

# =========================================================================
# 3. USE OWN PIN TO ACTIVATE
# =========================================================================

@router.post("/use")
def use_own_pin_to_activate(
    payload: PinUseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consumes 1 AVAILABLE PIN from user's inventory to activate their package."""
    try:
        result = pin_service.user_use_own_pin_to_activate(
            db=db,
            user_id=current_user.id,
            pin_id=payload.pin_id,
            raw_pin=payload.raw_pin
        )
        db.commit()
        return {
            "success": True,
            "message": "Package activated successfully with Security PIN! 30,000 BV credited.",
            "data": result
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =========================================================================
# 4. TRANSFER PIN TO DOWNLINE (GIVE PIN)
# =========================================================================

@router.post("/transfer")
def transfer_pin_to_downline(
    payload: PinTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfers available PIN(s) to an eligible downline network member."""
    try:
        transferred = pin_service.user_transfer_pin_to_downline(
            db=db,
            from_user_id=current_user.id,
            to_user_identifier=payload.to_user_identifier,
            pin_id=payload.pin_id,
            quantity=payload.quantity,
            reason=payload.reason or "Downline Package Activation"
        )
        db.commit()
        return {
            "success": True,
            "message": f"Successfully transferred {len(transferred)} Security PIN(s) to downline.",
            "data": transferred
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =========================================================================
# 5. UPLINE PIN REQUESTS
# =========================================================================

@router.post("/request-from-upline")
def request_pin_from_upline(
    payload: PinUplineRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sends a request to sponsor/upline requesting Security PINs."""
    try:
        req = pin_service.request_pin_from_upline(
            db=db,
            requester_user_id=current_user.id,
            upline_id=payload.upline_id,
            package_id=payload.package_id,
            quantity=payload.quantity,
            notes=payload.notes
        )
        db.commit()
        db.refresh(req)
        return {
            "success": True,
            "message": f"PIN Request {req.request_code} sent to upline for approval.",
            "data": req.to_dict()
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/upline-requests")
def list_upline_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns incoming requests (from downlines) and outgoing requests (to upline)."""
    incoming = db.query(SecurityPinUplineRequest).filter(
        SecurityPinUplineRequest.upline_user_id == current_user.id
    ).order_by(SecurityPinUplineRequest.id.desc()).all()

    outgoing = db.query(SecurityPinUplineRequest).filter(
        SecurityPinUplineRequest.requester_user_id == current_user.id
    ).order_by(SecurityPinUplineRequest.id.desc()).all()

    return {
        "success": True,
        "data": {
            "incoming": [r.to_dict() for r in incoming],
            "outgoing": [r.to_dict() for r in outgoing]
        }
    }

@router.post("/upline-requests/{id}/approve")
def approve_upline_request(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approves an incoming downline PIN request and transfers the requested PIN(s)."""
    try:
        result = pin_service.upline_approve_pin_request(
            db=db,
            request_id=id,
            upline_user_id=current_user.id
        )
        db.commit()
        return {
            "success": True,
            "message": "PIN request approved and PIN(s) transferred successfully!",
            "data": result
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/upline-requests/{id}/reject")
def reject_upline_request(
    id: int,
    payload: PinUplineRequestRespond,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rejects an incoming downline PIN request."""
    try:
        req = pin_service.upline_reject_pin_request(
            db=db,
            request_id=id,
            upline_user_id=current_user.id,
            reason=payload.notes or "Declined by upline"
        )
        db.commit()
        db.refresh(req)
        return {
            "success": True,
            "message": "PIN request rejected.",
            "data": req.to_dict()
        }
    except (PinValidationError, PinSecurityError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =========================================================================
# 6. PIN HISTORY & AUDIT LEDGER
# =========================================================================

@router.get("/history")
def get_user_pin_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns complete history of transfers and ledger actions for the current user."""
    transfers = db.query(SecurityPinTransfer).filter(
        or_(
            SecurityPinTransfer.from_user_id == current_user.id,
            SecurityPinTransfer.to_user_id == current_user.id
        )
    ).order_by(SecurityPinTransfer.id.desc()).all()

    ledger_entries = db.query(SecurityPinLedger).filter(
        SecurityPinLedger.user_id == current_user.id
    ).order_by(SecurityPinLedger.id.desc()).limit(100).all()

    return {
        "success": True,
        "data": {
            "transfers": [t.to_dict() for t in transfers],
            "ledger": [l.to_dict() for l in ledger_entries]
        }
    }
