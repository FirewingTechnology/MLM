from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.package import Package
from app.models.activation_request import PackageActivationRequest
from app.schemas.activation import (
    CreateActivationRequest,
    SubmitPaymentRequest,
    ActivateWithPinRequest
)
from app.security import get_current_user
from app.services.pin_service import pin_service, PinSecurityError, PinValidationError
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/package", tags=["package-activation"])

@router.post("/activation-request", status_code=201)
def create_activation_request(
    req: CreateActivationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        activation_req = pin_service.get_or_create_activation_request(
            db=db,
            user_id=current_user.id,
            package_id=req.package_id,
            payment_method=req.payment_method or "UPI_TRANSFER",
            payment_reference=req.payment_reference,
            payment_proof_url=req.payment_proof_url,
            admin_notes=req.notes
        )
        db.commit()
        return success_response(
            activation_req.to_dict(),
            "Package activation request created. Please submit payment details to receive your Security PIN.",
            201
        )
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("REQUEST_FAILED", str(e), 400)

@router.post("/payment-submit")
def submit_payment(
    req: SubmitPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        activation_req = pin_service.submit_payment(
            db=db,
            user_id=current_user.id,
            request_id=req.request_id,
            payment_method=req.payment_method or "UPI_TRANSFER",
            payment_reference=req.payment_reference,
            payment_proof_url=req.payment_proof_url
        )
        db.commit()
        return success_response(
            activation_req.to_dict(),
            "Payment reference submitted for verification. Admin will issue your Security PIN upon review."
        )
    except (PinSecurityError, Exception) as e:
        db.rollback()
        return error_response("PAYMENT_SUBMIT_FAILED", str(e), 400)

@router.get("/activation-status")
def get_activation_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    package = db.query(Package).filter(Package.is_active == True).first()
    
    latest_req = db.query(PackageActivationRequest).filter(
        PackageActivationRequest.user_id == current_user.id
    ).order_by(PackageActivationRequest.id.desc()).first()

    # Recipient info for payment transfer (sponsor or Matching parent)
    recipient = current_user.sponsor or current_user.binary_parent
    recipient_info = {
        'id': recipient.id if recipient else None,
        'full_name': recipient.full_name if recipient else 'Platform Franchise Admin',
        'user_code': recipient.user_code if recipient else 'ADMIN-001',
        'role': recipient.role if recipient else 'ADMIN',
        'relationship': 'Direct Sponsor' if (current_user.sponsor and recipient.id == current_user.sponsor.id) else 'Placement Parent'
    }

    status_data = {
        'is_active': current_user.is_active,
        'package': package.to_dict() if package else {
            'name': 'Premium Sub Franchise Package',
            'price': 35000.0,
            'product_value': 30000.0,
            'gst_amount': 5000.0,
            'bv': 30000.0
        },
        'activation_request': latest_req.to_dict() if latest_req else None,
        'payment_recipient': recipient_info,
        'can_activate_with_pin': latest_req is not None and latest_req.status in ('PIN_ISSUED', 'PAYMENT_VERIFIED') and not current_user.is_active
    }
    return success_response(status_data)

@router.post("/activate")
def activate_package_with_pin(
    req: ActivateWithPinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = pin_service.activate_package_with_pin(
            db=db,
            user_id=current_user.id,
            raw_pin=req.pin,
            request_id=req.request_id
        )
        db.commit()
        return success_response(
            result,
            f"Security PIN verified! Package successfully activated (+{result['purchase']['bv']:,.0f} BV)."
        )
    except PinValidationError as e:
        return error_response("INVALID_PIN", str(e), 400)
    except Exception as e:
        db.rollback()
        return error_response("ACTIVATION_FAILED", str(e), 400)
