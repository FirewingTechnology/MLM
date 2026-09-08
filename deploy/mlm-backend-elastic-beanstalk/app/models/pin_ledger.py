from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SecurityPinLedger(Base):
    __tablename__ = 'security_pin_ledger'

    id = Column(Integer, primary_key=True, index=True)
    pin_id = Column(Integer, ForeignKey('security_pins.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    # Actions: PIN_PURCHASED, PIN_ISSUED, PIN_RECEIVED, PIN_TRANSFERRED, PIN_TRANSFER_RECEIVED, PIN_USED, PIN_EXPIRED, PIN_REVOKED
    
    reference_id = Column(String(64), nullable=True)
    from_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    to_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    pin = relationship('SecurityPin')
    user = relationship('User', foreign_keys=[user_id])
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])
    actor = relationship('User', foreign_keys=[actor_id])

    def to_dict(self):
        return {
            'id': self.id,
            'pin_id': self.pin_id,
            'pin_code': self.pin.pin_code if self.pin else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'action': self.action,
            'reference_id': self.reference_id,
            'from_user_id': self.from_user_id,
            'from_user_name': self.from_user.full_name if self.from_user else None,
            'to_user_id': self.to_user_id,
            'to_user_name': self.to_user.full_name if self.to_user else None,
            'actor_id': self.actor_id,
            'actor_name': self.actor.full_name if self.actor else None,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
