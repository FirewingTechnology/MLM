from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class PackageActivationRequest(Base):
    __tablename__ = 'package_activation_requests'

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    
    package_amount = Column(Float, nullable=False, default=35000.0)
    package_bv = Column(Float, nullable=False, default=30000.0)
    
    payment_method = Column(String(50), default='UPI_TRANSFER', nullable=False)
    payment_reference = Column(String(100), nullable=True, index=True)
    payment_recipient_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    payment_proof_url = Column(String(255), nullable=True)
    
    status = Column(String(30), default='PAYMENT_SUBMITTED', nullable=False, index=True)
    # Statuses: PAYMENT_PENDING, PAYMENT_SUBMITTED, UNDER_REVIEW, PAYMENT_VERIFIED, PIN_ISSUED, ACTIVATED, REJECTED, CANCELLED
    
    admin_notes = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    security_pin_id = Column(Integer, ForeignKey('security_pins.id', ondelete='SET NULL', use_alter=True, name='fk_activation_req_pin_id'), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='activation_requests')
    package = relationship('Package')
    recipient = relationship('User', foreign_keys=[payment_recipient_id])
    verifier = relationship('User', foreign_keys=[verified_by])
    security_pin = relationship('SecurityPin', foreign_keys=[security_pin_id], post_update=True)
    purchase = relationship('Purchase')

    def to_dict(self):
        return {
            'id': self.id,
            'request_code': self.request_code,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'user_email': self.user.email if self.user else None,
            'sponsor_name': self.user.sponsor.full_name if (self.user and self.user.sponsor) else None,
            'sponsor_code': self.user.sponsor.user_code if (self.user and self.user.sponsor) else None,
            'binary_parent_name': self.user.binary_parent.full_name if (self.user and self.user.binary_parent) else None,
            'binary_parent_code': self.user.binary_parent.user_code if (self.user and self.user.binary_parent) else None,
            'binary_position': self.user.binary_position if self.user else None,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else 'Premium Sub Franchise Package',
            'package_amount': self.package_amount,
            'package_bv': self.package_bv,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'payment_recipient_id': self.payment_recipient_id,
            'payment_recipient_name': self.recipient.full_name if self.recipient else None,
            'payment_proof_url': self.payment_proof_url,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'rejection_reason': self.rejection_reason,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by_name': self.verifier.full_name if self.verifier else None,
            'security_pin_id': self.security_pin_id,
            'pin_status': self.security_pin.status if self.security_pin else None,
            'pin_code': self.security_pin.pin_code if self.security_pin else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'purchase_id': self.purchase_id
        }
