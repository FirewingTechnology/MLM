from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    total_earned = Column(Float, default=0.0, nullable=False)
    total_withdrawn = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='wallet')
    transactions = relationship('WalletTransaction', back_populates='wallet', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'balance': self.balance,
            'total_earned': self.total_earned,
            'total_withdrawn': self.total_withdrawn,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WalletTransaction(Base):
    __tablename__ = 'wallet_transactions'

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey('wallets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    transaction_type = Column(String(20), nullable=False, index=True)  # 'CREDIT', 'DEBIT', 'ADMIN_ADJUSTMENT'
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    
    category = Column(String(50), nullable=False)  # 'DIRECT_COMMISSION', 'MATCHING_COMMISSION', 'WITHDRAWAL', 'ADMIN_ADJUSTMENT'
    slot_id = Column(String(32), nullable=True, index=True)
    reference_id = Column(String(64), nullable=True, index=True)
    description = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    wallet = relationship('Wallet', back_populates='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'balance_before': self.balance_before,
            'balance_after': self.balance_after,
            'category': self.category,
            'slot_id': self.slot_id,
            'reference_id': self.reference_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

