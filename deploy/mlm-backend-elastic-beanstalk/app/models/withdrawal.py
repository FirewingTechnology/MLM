import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Withdrawal(Base):
    __tablename__ = 'withdrawals'

    id = Column(Integer, primary_key=True, index=True)
    withdrawal_code = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default='PENDING', nullable=False, index=True)  # 'PENDING', 'APPROVED', 'REJECTED'
    payout_method = Column(String(32), default='VIRTUAL_UPI', nullable=False)  # 'VIRTUAL_UPI', 'VIRTUAL_BANK'
    
    _payout_details = Column('payout_details', Text, nullable=True)
    admin_notes = Column(String(255), nullable=True)
    approved_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship('User', foreign_keys=[user_id], back_populates='withdrawals')
    approver = relationship('User', foreign_keys=[approved_by])

    @property
    def payout_details(self):
        if self._payout_details:
            try:
                return json.loads(self._payout_details)
            except Exception:
                return {}
        return {}

    @payout_details.setter
    def payout_details(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            self._payout_details = json.dumps(value)
        else:
            self._payout_details = value

    def to_dict(self):
        return {
            'id': self.id,
            'withdrawal_code': self.withdrawal_code,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'amount': self.amount,
            'status': self.status,
            'payout_method': self.payout_method,
            'payout_details': self.payout_details,
            'admin_notes': self.admin_notes,
            'approved_by': self.approved_by,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
