from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class BinaryPeriodVolume(Base):
    __tablename__ = 'binary_period_volumes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_id = Column(String(32), nullable=False, index=True)
    
    starting_carry_left = Column(Float, default=0.0, nullable=False)
    starting_carry_right = Column(Float, default=0.0, nullable=False)
    
    current_left_bv = Column(Float, default=0.0, nullable=False)
    current_right_bv = Column(Float, default=0.0, nullable=False)
    
    effective_left_bv = Column(Float, default=0.0, nullable=False)
    effective_right_bv = Column(Float, default=0.0, nullable=False)
    
    pair_completed = Column(Boolean, default=False, nullable=False)
    pair_bonus = Column(Float, default=0.0, nullable=False)
    
    consumed_left_bv = Column(Float, default=0.0, nullable=False)
    consumed_right_bv = Column(Float, default=0.0, nullable=False)
    
    ending_carry_left = Column(Float, default=0.0, nullable=False)
    ending_carry_right = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'slot_id', name='uq_user_slot_volume'),
    )

    user = relationship('User', back_populates='period_volumes')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'slot_id': self.slot_id,
            'starting_carry_left': self.starting_carry_left,
            'starting_carry_right': self.starting_carry_right,
            'current_left_bv': self.current_left_bv,
            'current_right_bv': self.current_right_bv,
            'effective_left_bv': self.effective_left_bv,
            'effective_right_bv': self.effective_right_bv,
            'pair_completed': self.pair_completed,
            'pair_bonus': self.pair_bonus,
            'consumed_left_bv': self.consumed_left_bv,
            'consumed_right_bv': self.consumed_right_bv,
            'ending_carry_left': self.ending_carry_left,
            'ending_carry_right': self.ending_carry_right,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
