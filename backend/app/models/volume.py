from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class BinaryVolume(Base):
    __tablename__ = 'binary_volumes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    
    accumulated_left_bv = Column(Float, default=0.0, nullable=False)
    accumulated_right_bv = Column(Float, default=0.0, nullable=False)
    
    carry_left_bv = Column(Float, default=0.0, nullable=False)
    carry_right_bv = Column(Float, default=0.0, nullable=False)
    
    matched_bv = Column(Float, default=0.0, nullable=False)
    personal_bv = Column(Float, default=0.0, nullable=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='volume')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'accumulated_left_bv': self.accumulated_left_bv,
            'accumulated_right_bv': self.accumulated_right_bv,
            'carry_left_bv': self.carry_left_bv,
            'carry_right_bv': self.carry_right_bv,
            'matched_bv': self.matched_bv,
            'personal_bv': self.personal_bv,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
