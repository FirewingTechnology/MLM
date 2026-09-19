from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SecurityPin(Base):
    __tablename__ = 'security_pins'

    id = Column(Integer, primary_key=True, index=True)
    pin_code = Column(String(32), unique=True, nullable=False, index=True) # Public Reference Code, e.g. SPIN-XXXX
    pin_hash = Column(String(128), unique=True, nullable=False, index=True) # SHA-256 hash of secret PIN
    
    # Ownership & Inventory
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True) # For backward-compatibility (same as owner_user_id)
    owner_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True) # Current owner
    original_owner_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True) # Original purchaser
    
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    activation_request_id = Column(Integer, ForeignKey('package_activation_requests.id', ondelete='SET NULL'), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey('security_pin_orders.id', ondelete='SET NULL'), nullable=True, index=True) # Purchase batch order
    
    amount = Column(Float, nullable=False, default=35400.0)
    bv = Column(Float, nullable=False, default=30000.0)
    
    status = Column(String(20), default='AVAILABLE', nullable=False, index=True)
    # Statuses: AVAILABLE, ISSUED (legacy alias for AVAILABLE), TRANSFERRED, USED, EXPIRED, REVOKED
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    transferred_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30), nullable=False)
    
    created_by_admin_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    payment_verified_at = Column(DateTime, nullable=True)
    
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    revocation_reason = Column(String(255), nullable=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    owner = relationship('User', foreign_keys=[owner_user_id], backref='owned_pins')
    original_owner = relationship('User', foreign_keys=[original_owner_user_id])
    package = relationship('Package')
    activation_request = relationship('PackageActivationRequest', foreign_keys=[activation_request_id])
    order = relationship('SecurityPinOrder', back_populates='pins', foreign_keys=[order_id])
    created_by_admin = relationship('User', foreign_keys=[created_by_admin_id])

    def to_dict(self, include_pin_code=True):
        masked_code = f"SPIN-****{self.pin_code[-4:]}" if self.pin_code and len(self.pin_code) >= 4 else self.pin_code
        return {
            'id': self.id,
            'pin_code': self.pin_code if include_pin_code else masked_code,
            'masked_code': masked_code,
            'user_id': self.user_id,
            'owner_user_id': self.owner_user_id,
            'owner_user_name': self.owner.full_name if self.owner else (self.user.full_name if self.user else None),
            'owner_user_code': self.owner.user_code if self.owner else (self.user.user_code if self.user else None),
            'original_owner_user_id': self.original_owner_user_id,
            'original_owner_name': self.original_owner.full_name if self.original_owner else None,
            'order_id': self.order_id,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'activation_request_id': self.activation_request_id,
            'amount': self.amount,
            'bv': self.bv,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'transferred_at': self.transferred_at.isoformat() if self.transferred_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by_admin_id': self.created_by_admin_id,
            'created_by_admin_name': self.created_by_admin.full_name if self.created_by_admin else None,
            'payment_reference': self.payment_reference,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
            'revocation_reason': self.revocation_reason
        }
