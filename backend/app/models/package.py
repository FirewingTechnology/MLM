from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Package(Base):
    __tablename__ = 'packages'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    price = Column(Float, nullable=False)           # ₹35,000
    product_value = Column(Float, nullable=False)   # ₹30,000
    gst_amount = Column(Float, nullable=False)      # ₹5,000
    bv = Column(Float, nullable=False)              # 30,000 BV
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchases = relationship('Purchase', back_populates='package')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'product_value': self.product_value,
            'gst_amount': self.gst_amount,
            'bv': self.bv,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
