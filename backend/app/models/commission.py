import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Commission(Base):
    __tablename__ = 'commissions'

    id = Column(Integer, primary_key=True, index=True)
    beneficiary_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    source_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'), nullable=True)
    
    commission_type = Column(String(32), nullable=False, index=True)  # 'DIRECT_REFERRAL', 'BINARY_MATCHING'
    slot_id = Column(String(32), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    bv_basis = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    
    _calculation_details = Column('calculation_details', Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    beneficiary = relationship('User', foreign_keys=[beneficiary_id], back_populates='commissions')
    source_user = relationship('User', foreign_keys=[source_user_id])
    purchase = relationship('Purchase')

    @property
    def calculation_details(self):
        if self._calculation_details:
            try:
                return json.loads(self._calculation_details)
            except Exception:
                return {}
        return {}

    @calculation_details.setter
    def calculation_details(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            self._calculation_details = json.dumps(value)
        else:
            self._calculation_details = value

    def to_dict(self):
        return {
            'id': self.id,
            'beneficiary_id': self.beneficiary_id,
            'source_user_id': self.source_user_id,
            'source_user_name': self.source_user.full_name if self.source_user else None,
            'source_user_code': self.source_user.user_code if self.source_user else None,
            'purchase_id': self.purchase_id,
            'commission_type': self.commission_type,
            'slot_id': self.slot_id,
            'amount': self.amount,
            'bv_basis': self.bv_basis,
            'percentage': self.percentage,
            'calculation_details': self.calculation_details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

