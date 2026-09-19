from typing import Optional, Dict, Any
from pydantic import BaseModel

class PurchaseRequest(BaseModel):
    package_id: Optional[int] = None
    amount: Optional[float] = None
    idempotency_key: Optional[str] = None

class WithdrawalRequest(BaseModel):
    amount: float
    payout_method: Optional[str] = "VIRTUAL_UPI"
    payout_details: Optional[Dict[str, Any]] = None

class AdminApprovalRequest(BaseModel):
    notes: Optional[str] = None

class WalletAdjustmentRequest(BaseModel):
    amount: float
    reason: str

class UserStatusRequest(BaseModel):
    is_active: bool
