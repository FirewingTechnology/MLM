from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ReferralToken(Base):
    __tablename__ = 'referral_tokens'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    sponsor_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    placement_side = Column(String(10), nullable=False)  # 'LEFT' or 'RIGHT'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sponsor = relationship('User', backref='referral_tokens')

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'sponsor_user_id': self.sponsor_user_id,
            'sponsor_name': self.sponsor.full_name if self.sponsor else None,
            'sponsor_code': self.sponsor.user_code if self.sponsor else None,
            'referral_code': self.sponsor.referral_code if self.sponsor else None,
            'placement_side': self.placement_side,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
