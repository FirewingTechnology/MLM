from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VolumeLedger(Base):
    __tablename__ = 'volume_ledgers'

    id = Column(Integer, primary_key=True, index=True)
    source_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    ancestor_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    side = Column(String(10), nullable=False, index=True)  # 'LEFT' or 'RIGHT'
    
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'), nullable=True, index=True)
    source_reference = Column(String(64), nullable=True, index=True)
    slot_id = Column(String(32), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    consumed_amount = Column(Float, default=0.0, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)  # 'ACTIVE', 'CONSUMED'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_user = relationship('User', foreign_keys=[source_user_id])
    ancestor_user = relationship('User', foreign_keys=[ancestor_user_id], back_populates='volume_ledger_entries')
    purchase = relationship('Purchase')

    def to_dict(self):
        return {
            'id': self.id,
            'source_user_id': self.source_user_id,
            'source_user_name': self.source_user.full_name if self.source_user else None,
            'source_user_code': self.source_user.user_code if self.source_user else None,
            'ancestor_user_id': self.ancestor_user_id,
            'ancestor_user_name': self.ancestor_user.full_name if self.ancestor_user else None,
            'ancestor_user_code': self.ancestor_user.user_code if self.ancestor_user else None,
            'side': self.side,
            'purchase_id': self.purchase_id,
            'source_reference': self.source_reference,
            'slot_id': self.slot_id,
            'amount': self.amount,
            'consumed_amount': self.consumed_amount,
            'remaining_amount': self.remaining_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
