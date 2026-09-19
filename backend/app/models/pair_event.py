from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PairEvent(Base):
    __tablename__ = 'pair_events'

    id = Column(Integer, primary_key=True, index=True)
    pair_earner_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_id = Column(String(32), nullable=False, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'), nullable=True)
    
    left_source_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    right_source_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    matched_left_bv = Column(Float, default=30000.0, nullable=False)
    matched_right_bv = Column(Float, default=30000.0, nullable=False)
    pair_bonus = Column(Float, default=10000.0, nullable=False)
    
    matching_upline_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    matching_commission = Column(Float, default=0.0, nullable=False)
    
    status = Column(String(32), default='COMPLETED', nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pair_earner = relationship('User', foreign_keys=[pair_earner_user_id])
    matching_upline = relationship('User', foreign_keys=[matching_upline_id])
    purchase = relationship('Purchase')

    def to_dict(self):
        return {
            'id': self.id,
            'pair_earner_user_id': self.pair_earner_user_id,
            'slot_id': self.slot_id,
            'purchase_id': self.purchase_id,
            'left_source_user_id': self.left_source_user_id,
            'right_source_user_id': self.right_source_user_id,
            'matched_left_bv': self.matched_left_bv,
            'matched_right_bv': self.matched_right_bv,
            'pair_bonus': self.pair_bonus,
            'matching_upline_id': self.matching_upline_id,
            'matching_commission': self.matching_commission,
            'status': self.status,
            'idempotency_key': self.idempotency_key,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
