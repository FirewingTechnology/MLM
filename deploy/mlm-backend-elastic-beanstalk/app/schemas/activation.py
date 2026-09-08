from typing import Optional
from pydantic import BaseModel, Field

class CreateActivationRequest(BaseModel):
    package_id: Optional[int] = None
    payment_method: Optional[str] = "UPI_TRANSFER"
    payment_reference: Optional[str] = None
    payment_proof_url: Optional[str] = None
    notes: Optional[str] = None

class SubmitPaymentRequest(BaseModel):
    request_id: Optional[int] = None
    payment_method: Optional[str] = "UPI_TRANSFER"
    payment_reference: str = Field(..., min_length=2, max_length=100)
    payment_proof_url: Optional[str] = None

class ActivateWithPinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=64)
    request_id: Optional[int] = None

class AdminVerifyPaymentRequest(BaseModel):
    admin_notes: Optional[str] = None

class AdminIssuePinRequest(BaseModel):
    expires_in_days: Optional[int] = 7
    notes: Optional[str] = None

class AdminRejectRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=255)

class AdminRevokePinRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=255)
