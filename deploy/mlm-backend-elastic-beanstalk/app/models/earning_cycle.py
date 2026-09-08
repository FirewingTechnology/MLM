from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class EarningCycle(Base):
    __tablename__ = 'earning_cycles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='SET NULL'), nullable=True)
    cycle_number = Column(Integer, nullable=False, default=1)
    
    direct_income = Column(Float, nullable=False, default=0.0)
    pairing_income = Column(Float, nullable=False, default=0.0)
    total_eligible_income = Column(Float, nullable=False, default=0.0)
    earning_cap = Column(Float, nullable=False, default=300000.0)
    
    status = Column(String(32), nullable=False, default='ACTIVE')  # 'ACTIVE', 'RETOPUP_REQUIRED', 'COMPLETED'
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    capped_at = Column(DateTime, nullable=True)
    reset_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='earning_cycles')
    package = relationship('Package')

    __table_args__ = (
        UniqueConstraint('user_id', 'cycle_number', name='uq_user_earning_cycle'),
    )

    @property
    def remaining_capacity(self) -> float:
        return max(0.0, round(self.earning_cap - self.total_eligible_income, 2))

    @property
    def progress_percentage(self) -> float:
        if self.earning_cap <= 0:
            return 100.0
        return min(100.0, round((self.total_eligible_income / self.earning_cap) * 100.0, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'cycle_number': self.cycle_number,
            'direct_income': self.direct_income,
            'pairing_income': self.pairing_income,
            'total_eligible_income': self.total_eligible_income,
            'earning_cap': self.earning_cap,
            'remaining_capacity': self.remaining_capacity,
            'progress_percentage': self.progress_percentage,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'capped_at': self.capped_at.isoformat() if self.capped_at else None,
            'reset_at': self.reset_at.isoformat() if self.reset_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
