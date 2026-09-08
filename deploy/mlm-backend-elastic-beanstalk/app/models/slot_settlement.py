from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class SlotSettlement(Base):
    __tablename__ = 'slot_settlements'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_id = Column(String(32), nullable=False, index=True)
    
    left_before = Column(Float, default=0.0, nullable=False)
    right_before = Column(Float, default=0.0, nullable=False)
    
    left_matched = Column(Float, default=0.0, nullable=False)
    right_matched = Column(Float, default=0.0, nullable=False)
    
    pairs_paid = Column(Integer, default=0, nullable=False)
    pair_bonus = Column(Float, default=0.0, nullable=False)
    
    left_carry = Column(Float, default=0.0, nullable=False)
    right_carry = Column(Float, default=0.0, nullable=False)
    
    carry_commission = Column(Float, default=0.0, nullable=False)
    matching_commission = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default='SETTLED', nullable=False)  # 'SETTLED', 'FINALIZED'
    
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'slot_id', name='uq_user_slot_settlement'),
    )

    user = relationship('User', back_populates='slot_settlements')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'slot_id': self.slot_id,
            'left_before': self.left_before,
            'right_before': self.right_before,
            'left_matched': self.left_matched,
            'right_matched': self.right_matched,
            'pairs_paid': self.pairs_paid,
            'pair_bonus': self.pair_bonus,
            'left_carry': self.left_carry,
            'right_carry': self.right_carry,
            'carry_commission': self.carry_commission,
            'matching_commission': self.matching_commission,
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
