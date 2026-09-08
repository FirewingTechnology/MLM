from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SecurityPinTransfer(Base):
    __tablename__ = 'security_pin_transfers'

    id = Column(Integer, primary_key=True, index=True)
    pin_id = Column(Integer, ForeignKey('security_pins.id', ondelete='CASCADE'), nullable=False, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    transfer_reason = Column(String(255), nullable=True)
    transferred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default='COMPLETED', nullable=False)

    # Relationships
    pin = relationship('SecurityPin', backref='transfers')
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])
    created_by = relationship('User', foreign_keys=[created_by_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'pin_id': self.pin_id,
            'pin_code': self.pin.pin_code if self.pin else None,
            'from_user_id': self.from_user_id,
            'from_user_name': self.from_user.full_name if self.from_user else None,
            'from_user_code': self.from_user.user_code if self.from_user else None,
            'to_user_id': self.to_user_id,
            'to_user_name': self.to_user.full_name if self.to_user else None,
            'to_user_code': self.to_user.user_code if self.to_user else None,
            'transfer_reason': self.transfer_reason,
            'transferred_at': self.transferred_at.isoformat() if self.transferred_at else None,
            'status': self.status
        }
