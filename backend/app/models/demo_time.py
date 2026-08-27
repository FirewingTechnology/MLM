from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class DemoTimeConfig(Base):
    __tablename__ = 'demo_time_config'

    id = Column(Integer, primary_key=True, default=1)
    mode = Column(String(10), default='REAL', nullable=False)  # 'REAL', 'DEMO'
    virtual_datetime = Column(DateTime, nullable=True)  # Store datetime in IST representation
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    updater = relationship('User', foreign_keys=[updated_by])

    def to_dict(self):
        return {
            'id': self.id,
            'mode': self.mode,
            'virtual_datetime': self.virtual_datetime.isoformat() if self.virtual_datetime else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
