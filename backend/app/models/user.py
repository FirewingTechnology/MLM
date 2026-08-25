from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    mobile = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='USER')  # 'USER', 'ADMIN'
    referral_code = Column(String(32), unique=True, nullable=False, index=True)
    
    # Sponsor (Referral) Relationship
    sponsor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Binary Tree Placement Relationship
    binary_parent_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    binary_position = Column(String(10), nullable=True)  # 'LEFT', 'RIGHT', or None for root
    
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sponsor = relationship('User', foreign_keys=[sponsor_id], remote_side=[id], backref='sponsored_users')
    binary_parent = relationship('User', foreign_keys=[binary_parent_id], remote_side=[id], backref='binary_children')
    
    wallet = relationship('Wallet', back_populates='user', uselist=False, cascade='all, delete-orphan')
    volume = relationship('BinaryVolume', back_populates='user', uselist=False, cascade='all, delete-orphan')
    purchases = relationship('Purchase', back_populates='user', cascade='all, delete-orphan')
    commissions = relationship('Commission', foreign_keys='Commission.beneficiary_id', back_populates='beneficiary')
    withdrawals = relationship('Withdrawal', foreign_keys='Withdrawal.user_id', back_populates='user', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('binary_parent_id', 'binary_position', name='uq_binary_parent_position'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_code': self.user_code,
            'email': self.email,
            'mobile': self.mobile,
            'full_name': self.full_name,
            'role': self.role,
            'referral_code': self.referral_code,
            'sponsor_id': self.sponsor_id,
            'sponsor_name': self.sponsor.full_name if self.sponsor else None,
            'sponsor_code': self.sponsor.user_code if self.sponsor else None,
            'binary_parent_id': self.binary_parent_id,
            'binary_parent_name': self.binary_parent.full_name if self.binary_parent else None,
            'binary_parent_code': self.binary_parent.user_code if self.binary_parent else None,
            'binary_position': self.binary_position,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'wallet_balance': self.wallet.balance if self.wallet else 0.0,
            'left_bv': self.volume.accumulated_left_bv if self.volume else 0.0,
            'right_bv': self.volume.accumulated_right_bv if self.volume else 0.0,
            'carry_left_bv': self.volume.carry_left_bv if self.volume else 0.0,
            'carry_right_bv': self.volume.carry_right_bv if self.volume else 0.0,
            'matched_bv': self.volume.matched_bv if self.volume else 0.0,
            'personal_bv': self.volume.personal_bv if self.volume else 0.0,
        }
