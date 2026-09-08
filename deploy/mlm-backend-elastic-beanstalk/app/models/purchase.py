from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Purchase(Base):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True, index=True)
    purchase_code = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    
    amount = Column(Float, nullable=False)          # ₹35,000
    product_value = Column(Float, default=30000.0, nullable=False)   # ₹30,000
    gst_amount = Column(Float, default=5000.0, nullable=False)      # ₹5,000
    bv = Column(Float, nullable=False)              # 30,000 BV
    status = Column(String(20), default='COMPLETED', nullable=False)
    slot_id = Column(String(32), nullable=True, index=True)
    idempotency_key = Column(String(64), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='purchases')
    package = relationship('Package', back_populates='purchases')

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_code': self.purchase_code,
            'user_id': self.user_id,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'amount': self.amount,
            'product_value': self.product_value,
            'gst_amount': self.gst_amount,
            'bv': self.bv,
            'status': self.status,
            'slot_id': self.slot_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

