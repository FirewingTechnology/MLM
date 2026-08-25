import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    _details = Column('details', Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship('User')

    @property
    def details(self):
        if self._details:
            try:
                return json.loads(self._details)
            except Exception:
                return {}
        return {}

    @details.setter
    def details(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            self._details = json.dumps(value)
        else:
            self._details = value

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System',
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
