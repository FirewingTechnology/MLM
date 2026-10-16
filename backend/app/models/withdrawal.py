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
    fee_percentage = Column(Float, default=15.0, nullable=False)
    fee_amount = Column(Float, default=0.0, nullable=False)
    net_amount = Column(Float, default=0.0, nullable=False)
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
        fee_pct = getattr(self, 'fee_percentage', None)
        if fee_pct is None:
            fee_pct = 15.0
        fee_amt = getattr(self, 'fee_amount', None)
        if fee_amt is None or fee_amt == 0.0:
            fee_amt = round(self.amount * (fee_pct / 100.0), 2)
        net_amt = getattr(self, 'net_amount', None)
        if net_amt is None or net_amt == 0.0:
            net_amt = round(self.amount - fee_amt, 2)

        return {
            'id': self.id,
            'withdrawal_code': self.withdrawal_code,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'amount': self.amount,
            'fee_percentage': fee_pct,
            'fee_amount': fee_amt,
            'net_amount': net_amt,
            'status': self.status,
            'payout_method': self.payout_method,
            'payout_details': self.payout_details,
            'admin_notes': self.admin_notes,
            'approved_by': self.approved_by,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
