from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base

class RankConfig(Base):
    __tablename__ = 'rank_configs'

    id = Column(Integer, primary_key=True, index=True)
    rank_name = Column(String(32), unique=True, nullable=False, index=True)  # 'STAR', 'SUPER_STAR', 'VIP'
    display_name = Column(String(64), nullable=False)  # 'Star', 'Super Star', 'VIP'
    level = Column(Integer, nullable=False, default=1)  # 1, 2, 3
    required_directs = Column(Integer, nullable=False, default=2)
    qualification_days = Column(Integer, nullable=False, default=7)
    reward_type = Column(String(32), nullable=False, default='CASH')  # 'CASH', 'EV_SCOOTER'
    reward_amount = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'rank_name': self.rank_name,
            'display_name': self.display_name,
            'level': self.level,
            'required_directs': self.required_directs,
            'qualification_days': self.qualification_days,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
