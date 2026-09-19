from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class DailyRewardCycle(Base):
    __tablename__ = 'daily_reward_cycles'

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey('packages.id', ondelete='RESTRICT'), nullable=False)
    
    refund_target = Column(Float, nullable=False, default=35400.0)
    refunded_amount = Column(Float, nullable=False, default=0.0)
    completed_pairs = Column(Integer, nullable=False, default=0)
    base_daily_amount = Column(Float, nullable=False, default=50.0)
    pair_increment = Column(Float, nullable=False, default=50.0)
    current_daily_reward = Column(Float, nullable=False, default=50.0)
    
    status = Column(String(32), nullable=False, default='ACTIVE', index=True)  # 'ACTIVE', 'COMPLETED'
    last_credit_date = Column(String(10), nullable=True, index=True)  # 'YYYY-MM-DD'
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='daily_reward_cycles')
    purchase = relationship('Purchase', back_populates='daily_reward_cycle')
    package = relationship('Package')
    transactions = relationship('DailyRewardTransaction', back_populates='cycle', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_daily_reward_cycle_user_status', 'user_id', 'status'),
        Index('ix_daily_reward_cycle_user_last_credit', 'user_id', 'last_credit_date'),
    )

    @property
    def remaining_refund(self) -> float:
        return max(0.0, round(self.refund_target - self.refunded_amount, 2))

    @property
    def progress_percentage(self) -> float:
        if self.refund_target <= 0:
            return 100.0
        return min(100.0, round((self.refunded_amount / self.refund_target) * 100.0, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'purchase_code': self.purchase.purchase_code if self.purchase else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'package_id': self.package_id,
            'package_name': self.package.name if self.package else None,
            'refund_target': self.refund_target,
            'refunded_amount': self.refunded_amount,
            'remaining_refund': self.remaining_refund,
            'completed_pairs': self.completed_pairs,
            'base_daily_amount': self.base_daily_amount,
            'pair_increment': self.pair_increment,
            'current_daily_reward': self.current_daily_reward,
            'progress_percentage': self.progress_percentage,
            'status': self.status,
            'last_credit_date': self.last_credit_date,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DailyRewardTransaction(Base):
    __tablename__ = 'daily_reward_transactions'

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey('daily_reward_cycles.id', ondelete='CASCADE'), nullable=False, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    business_date = Column(String(10), nullable=False, index=True)  # 'YYYY-MM-DD'
    amount = Column(Float, nullable=False)
    completed_pairs_snapshot = Column(Integer, nullable=False, default=0)
    daily_reward_snapshot = Column(Float, nullable=False, default=50.0)
    
    wallet_transaction_id = Column(Integer, ForeignKey('wallet_transactions.id', ondelete='SET NULL'), nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)  # 'DAILY_REFUND:{purchase_id}:{YYYY-MM-DD}'
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cycle = relationship('DailyRewardCycle', back_populates='transactions')
    purchase = relationship('Purchase')
    user = relationship('User')
    wallet_transaction = relationship('WalletTransaction')

    __table_args__ = (
        Index('ix_daily_reward_txn_user_date', 'user_id', 'business_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'cycle_id': self.cycle_id,
            'purchase_id': self.purchase_id,
            'user_id': self.user_id,
            'business_date': self.business_date,
            'amount': self.amount,
            'completed_pairs_snapshot': self.completed_pairs_snapshot,
            'daily_reward_snapshot': self.daily_reward_snapshot,
            'wallet_transaction_id': self.wallet_transaction_id,
            'idempotency_key': self.idempotency_key,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
