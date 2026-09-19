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
from app.config import settings
from app.services.pin_service import pin_service, PinSecurityError, PinValidationError
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/package", tags=["package-activation"])

@router.post("/activation-request", status_code=201)
def create_activation_request(
    req: CreateActivationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch authoritative package
    if req.package_id:
        target_package = db.get(Package, req.package_id)
    else:
        target_package = db.query(Package).filter(Package.is_active == True).first()

    if not target_package:
        return error_response("PACKAGE_NOT_FOUND", "No active package available.", 404)

    if req.amount is not None and abs(req.amount - target_package.price) > 0.01:
        return error_response(
            "INVALID_PACKAGE_AMOUNT",
            f"Invalid package payment amount ₹{req.amount:,.2f}. Authoritative package price is ₹{target_package.price:,.2f}.",
            400
        )

    try:
        activation_req = pin_service.get_or_create_activation_request(
            db=db,
            user_id=current_user.id,
            package_id=target_package.id,
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
    if req.amount is not None:
        target_package = db.query(Package).filter(Package.is_active == True).first()
        if target_package and abs(req.amount - target_package.price) > 0.01:
            return error_response(
                "INVALID_PACKAGE_AMOUNT",
                f"Invalid payment amount ₹{req.amount:,.2f}. Authoritative package price is ₹{target_package.price:,.2f}.",
                400
            )

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
            'name': 'Premium Sub Franchise',
            'price': 35400.0,
            'product_value': 30000.0,
            'gst_amount': 5400.0,
            'bv': 30000.0
        },
        'activation_request': latest_req.to_dict() if latest_req else None,
        'payment_recipient': recipient_info,
        'upi_details': {
            'upi_id': getattr(settings, 'COMPANY_UPI_ID', 'mystatusads@icici'),
            'payee_name': getattr(settings, 'COMPANY_UPI_NAME', 'MyStatus Platform'),
            'amount': package.price if package else 35400.0,
            'qr_image_url': '/payment-qr.png'
        },
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
