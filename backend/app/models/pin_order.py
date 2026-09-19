from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SecurityPinOrder(Base):
    __tablename__ = 'security_pin_orders'

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(32), unique=True, nullable=False, index=True) # e.g. SPO-20260829-XXXX
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    
    quantity = Column(Integer, nullable=False, default=1)
    price_per_pin = Column(Float, nullable=False, default=35400.0)
    total_amount = Column(Float, nullable=False, default=35400.0) # quantity * price_per_pin
    bv_per_pin = Column(Float, nullable=False, default=30000.0)
    
    payment_method = Column(String(50), default='UPI_TRANSFER', nullable=False)
    payment_reference = Column(String(100), nullable=True, index=True)
    payment_proof_url = Column(String(255), nullable=True)
    
    status = Column(String(30), default='PAYMENT_SUBMITTED', nullable=False, index=True)
    # Statuses: PAYMENT_PENDING, PAYMENT_SUBMITTED, UNDER_REVIEW, PAYMENT_VERIFIED, COMPLETED, REJECTED, CANCELLED
    
    admin_notes = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    buyer = relationship('User', foreign_keys=[user_id], backref='pin_orders')
    package = relationship('Package')
    verifier = relationship('User', foreign_keys=[verified_by])
    pins = relationship('SecurityPin', back_populates='order')

    def to_dict(self):
        return {
            'id': self.id,
            'order_code': self.order_code,
            'user_id': self.user_id,
            'user_name': self.buyer.full_name if self.buyer else None,
            'user_code': self.buyer.user_code if self.buyer else None,
            'user_email': self.buyer.email if self.buyer else None,
            'buyer_name': self.buyer.full_name if self.buyer else None,
            'buyer_code': self.buyer.user_code if self.buyer else None,
            'buyer_email': self.buyer.email if self.buyer else None,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else 'Premium Sub Franchise Package',
            'quantity': self.quantity,
            'price_per_pin': self.price_per_pin,
            'total_amount': self.total_amount,
            'bv_per_pin': self.bv_per_pin,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'payment_proof_url': self.payment_proof_url,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by_name': self.verifier.full_name if self.verifier else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'generated_pins_count': len(self.pins) if self.pins else 0
        }
