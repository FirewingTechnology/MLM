from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SecurityPinUplineRequest(Base):
    __tablename__ = 'security_pin_upline_requests'

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(32), unique=True, nullable=False, index=True)
    requester_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    upline_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    
    quantity = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default='PENDING', nullable=False, index=True)
    # Statuses: PENDING, APPROVED, REJECTED, CANCELLED
    
    notes = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    transferred_pin_id = Column(Integer, ForeignKey('security_pins.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    requester = relationship('User', foreign_keys=[requester_user_id], backref='outgoing_pin_requests')
    upline = relationship('User', foreign_keys=[upline_user_id], backref='incoming_pin_requests')
    package = relationship('Package')
    transferred_pin = relationship('SecurityPin', foreign_keys=[transferred_pin_id])

    def to_dict(self):
        return {
            'id': self.id,
            'request_code': self.request_code,
            'requester_user_id': self.requester_user_id,
            'requester_user_name': self.requester.full_name if self.requester else None,
            'requester_user_code': self.requester.user_code if self.requester else None,
            'upline_user_id': self.upline_user_id,
            'upline_user_name': self.upline.full_name if self.upline else None,
            'upline_user_code': self.upline.user_code if self.upline else None,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'quantity': self.quantity,
            'status': self.status,
            'notes': self.notes,
            'rejection_reason': self.rejection_reason,
            'transferred_pin_id': self.transferred_pin_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }
