from datetime import datetime
from sqlalchemy.orm import Session
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.services.audit_service import log_action

class InsufficientBalanceError(Exception):
    pass

class InvalidTransactionError(Exception):
    pass

def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0, total_earned=0.0, total_withdrawn=0.0)
        db.add(wallet)
        db.flush()
    return wallet

def credit_wallet(db: Session, user_id: int, amount: float, category: str, description: str, reference_id: str = None, slot_id: str = None) -> WalletTransaction:
    if amount <= 0:
        raise InvalidTransactionError("Credit amount must be strictly positive.")
        
    wallet = get_or_create_wallet(db, user_id)
    balance_before = wallet.balance
    wallet.balance += amount
    wallet.total_earned += amount
    balance_after = wallet.balance
    
    txn = WalletTransaction(
        wallet_id=wallet.id,
        user_id=user_id,
        transaction_type='CREDIT',
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        category=category,
        slot_id=slot_id,
        reference_id=reference_id,
        description=description
    )
    db.add(txn)
    db.flush()
    
    log_action(db, 'WALLET_CREDITED', 'Wallet', wallet.id, user_id, {
        'amount': amount,
        'category': category,
        'slot_id': slot_id,
        'reference_id': reference_id,
        'balance_after': balance_after
    })
    return txn

def debit_wallet(db: Session, user_id: int, amount: float, category: str, description: str, reference_id: str = None, slot_id: str = None) -> WalletTransaction:
    if amount <= 0:
        raise InvalidTransactionError("Debit amount must be strictly positive.")
        
    wallet = get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise InsufficientBalanceError(f"Insufficient wallet balance. Available: ₹{wallet.balance:,.2f}, Requested: ₹{amount:,.2f}")
        
    balance_before = wallet.balance
    wallet.balance -= amount
    if category == 'WITHDRAWAL':
        wallet.total_withdrawn += amount
    balance_after = wallet.balance
    
    txn = WalletTransaction(
        wallet_id=wallet.id,
        user_id=user_id,
        transaction_type='DEBIT',
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        category=category,
        slot_id=slot_id,
        reference_id=reference_id,
        description=description
    )
    db.add(txn)
    db.flush()
    
    log_action(db, 'WALLET_DEBITED', 'Wallet', wallet.id, user_id, {
        'amount': amount,
        'category': category,
        'slot_id': slot_id,
        'reference_id': reference_id,
        'balance_after': balance_after
    })
    return txn

def adjust_wallet_balance(db: Session, user_id: int, amount: float, admin_id: int, reason: str, slot_id: str = None) -> WalletTransaction:
    wallet = get_or_create_wallet(db, user_id)
    balance_before = wallet.balance
    new_balance = balance_before + amount
    if new_balance < 0:
        raise InsufficientBalanceError(f"Adjustment would result in negative balance: ₹{new_balance:,.2f}")
        
    wallet.balance = new_balance
    if amount > 0:
        wallet.total_earned += amount
    balance_after = wallet.balance
    
    txn = WalletTransaction(
        wallet_id=wallet.id,
        user_id=user_id,
        transaction_type='ADMIN_ADJUSTMENT',
        amount=abs(amount),
        balance_before=balance_before,
        balance_after=balance_after,
        category='ADMIN_ADJUSTMENT',
        slot_id=slot_id,
        reference_id=f"ADMIN-ADJ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        description=f"Admin Adjustment: {reason}"
    )
    db.add(txn)
    db.flush()
    
    log_action(db, 'WALLET_ADJUSTED', 'Wallet', wallet.id, admin_id, {
        'adjusted_user_id': user_id,
        'adjustment_amount': amount,
        'reason': reason,
        'slot_id': slot_id,
        'balance_after': balance_after
    })

    return txn

def create_withdrawal_request(db: Session, user_id: int, amount: float, payout_method: str = 'VIRTUAL_UPI', payout_details: dict = None) -> Withdrawal:
    if amount <= 0:
        raise InvalidTransactionError("Withdrawal amount must be greater than 0.")
        
    wallet = get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise InsufficientBalanceError(f"Cannot withdraw ₹{amount:,.2f}. Current balance is ₹{wallet.balance:,.2f}.")
        
    wdr_code = f"WDR-{abs(hash(f'{user_id}-{datetime.utcnow().timestamp()}')) % 1000000000:09d}"
    
    withdrawal = Withdrawal(
        withdrawal_code=wdr_code,
        user_id=user_id,
        amount=amount,
        status='PENDING',
        payout_method=payout_method,
        admin_notes=None
    )
    if payout_details:
        withdrawal.payout_details = payout_details
        
    db.add(withdrawal)
    db.flush()
    
    log_action(db, 'WITHDRAWAL_REQUESTED', 'Withdrawal', withdrawal.id, user_id, {
        'amount': amount,
        'code': wdr_code
    })
    return withdrawal

def approve_withdrawal(db: Session, withdrawal_id: int, admin_id: int, notes: str = None) -> Withdrawal:
    withdrawal = db.get(Withdrawal, withdrawal_id)
    if not withdrawal:
        raise InvalidTransactionError("Withdrawal record not found.")
    if withdrawal.status != 'PENDING':
        raise InvalidTransactionError(f"Cannot approve withdrawal in '{withdrawal.status}' state.")
        
    debit_wallet(
        db,
        user_id=withdrawal.user_id,
        amount=withdrawal.amount,
        category='WITHDRAWAL',
        description=f"Demo Payout for Request {withdrawal.withdrawal_code}",
        reference_id=withdrawal.withdrawal_code
    )
    
    withdrawal.status = 'APPROVED'
    withdrawal.approved_by = admin_id
    withdrawal.admin_notes = notes or "Approved by Admin"
    withdrawal.processed_at = datetime.utcnow()
    db.flush()
    
    log_action(db, 'WITHDRAWAL_APPROVED', 'Withdrawal', withdrawal.id, admin_id, {
        'user_id': withdrawal.user_id,
        'amount': withdrawal.amount
    })
    return withdrawal

def reject_withdrawal(db: Session, withdrawal_id: int, admin_id: int, notes: str = None) -> Withdrawal:
    withdrawal = db.get(Withdrawal, withdrawal_id)
    if not withdrawal:
        raise InvalidTransactionError("Withdrawal record not found.")
    if withdrawal.status != 'PENDING':
        raise InvalidTransactionError(f"Cannot reject withdrawal in '{withdrawal.status}' state.")
        
    withdrawal.status = 'REJECTED'
    withdrawal.approved_by = admin_id
    withdrawal.admin_notes = notes or "Rejected by Admin"
    withdrawal.processed_at = datetime.utcnow()
    db.flush()
    
    log_action(db, 'WITHDRAWAL_REJECTED', 'Withdrawal', withdrawal.id, admin_id, {
        'user_id': withdrawal.user_id,
        'amount': withdrawal.amount,
        'notes': notes
    })
    return withdrawal
