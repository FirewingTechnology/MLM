from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class RankAchievement(Base):
    __tablename__ = 'rank_achievements'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    rank_name = Column(String(32), nullable=False, index=True)  # 'STAR', 'SUPER_STAR', 'VIP'
    status = Column(String(32), nullable=False, default='IN_PROGRESS')  # 'IN_PROGRESS', 'ACHIEVED', 'EXPIRED'
    
    qualification_started_at = Column(DateTime, nullable=False)
    qualification_deadline = Column(DateTime, nullable=False)
    achieved_at = Column(DateTime, nullable=True)
    
    reward_type = Column(String(32), nullable=False, default='CASH')  # 'CASH', 'EV_SCOOTER'
    reward_amount = Column(Float, nullable=False, default=0.0)
    reward_status = Column(String(32), nullable=False, default='PENDING')  # 'PENDING', 'CREDITED', 'PENDING_FULFILLMENT', 'FULFILLED', 'REJECTED'
    reward_transaction_id = Column(Integer, ForeignKey('wallet_transactions.id', ondelete='SET NULL'), nullable=True)
    
    # Stores JSON array string of contributing direct member user IDs e.g. "[10, 11]"
    qualifying_direct_ids = Column(String(255), nullable=True)
    admin_notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='rank_achievements')
    reward_transaction = relationship('WalletTransaction')

    __table_args__ = (
        UniqueConstraint('user_id', 'rank_name', name='uq_user_rank_achievement'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_code': self.user.user_code if self.user else None,
            'rank_name': self.rank_name,
            'status': self.status,
            'qualification_started_at': self.qualification_started_at.isoformat() if self.qualification_started_at else None,
            'qualification_deadline': self.qualification_deadline.isoformat() if self.qualification_deadline else None,
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'reward_status': self.reward_status,
            'reward_transaction_id': self.reward_transaction_id,
            'qualifying_direct_ids': self.qualifying_direct_ids,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
