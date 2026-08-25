from typing import Optional
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    password: str
    confirm_password: str
    referral_code: str
    binary_parent_code: Optional[str] = None
    binary_position: Optional[str] = None  # 'LEFT', 'RIGHT', or None (auto)

class LoginRequest(BaseModel):
    identifier: str  # email or user_code
    password: str
