from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PinOrderCreateRequest(BaseModel):
    package_id: Optional[int] = 1
    quantity: int = Field(default=1, ge=1, le=500, description="Number of PINs to purchase")
    amount: Optional[float] = None
    payment_method: str = Field(default="UPI_TRANSFER")
    payment_reference: str = Field(..., min_length=3, max_length=100, description="UTR / Transaction Ref")
    payment_proof_url: Optional[str] = None

class PinOrderVerifyRequest(BaseModel):
    admin_notes: Optional[str] = None

class PinOrderRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=255)

class PinOrderIssueRequest(BaseModel):
    expires_in_days: int = Field(default=30, ge=1, le=365)

class PinTransferRequest(BaseModel):
    to_user_identifier: str = Field(..., description="Recipient user_code, email, or ID")
    pin_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1, le=100, description="Quantity of PINs to transfer")
    reason: Optional[str] = Field(default="Downline Package Activation", max_length=255)

class PinUplineRequestCreate(BaseModel):
    upline_id: Optional[int] = None # Defaults to direct sponsor
    package_id: Optional[int] = 1
    quantity: int = Field(default=1, ge=1, le=50)
    notes: Optional[str] = None

class PinUplineRequestRespond(BaseModel):
    notes: Optional[str] = None

class PinUseRequest(BaseModel):
    pin_id: Optional[int] = None
    raw_pin: Optional[str] = None # Optional if user owns the PIN in inventory and passes pin_id

class PinRevokeRequest(BaseModel):
    revocation_reason: str = Field(..., min_length=3, max_length=255)
