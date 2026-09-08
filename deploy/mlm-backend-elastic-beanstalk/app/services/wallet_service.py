from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.services.audit_service import log_action

class InsufficientBalanceError(Exception):
    pass

class InvalidTransactionError(Exception):
    pass

def get_or_create_wallet(db: Session, user_id: int, for_update: bool = False) -> Wallet:
    """
    Retrieves or creates a user's wallet with concurrency protection and optional FOR UPDATE row locking.
    Handles first-time concurrent creation races safely using savepoints (begin_nested).
    """
    query = db.query(Wallet).filter(Wallet.user_id == user_id)
    if for_update:
        query = query.with_for_update()

    wallet = query.first()
    if not wallet:
        try:
            # Use savepoint to handle simultaneous first-time wallet creation race safely
            with db.begin_nested():
                wallet = Wallet(user_id=user_id, balance=0.0, total_earned=0.0, total_withdrawn=0.0)
                db.add(wallet)
                db.flush()
        except IntegrityError:
            # Another concurrent request already inserted the wallet row
            query = db.query(Wallet).filter(Wallet.user_id == user_id)
            if for_update:
                query = query.with_for_update()
            wallet = query.first()

    return wallet

def credit_wallet(
    db: Session,
    user_id: int,
    amount: float,
    category: str,
    description: str,
    reference_id: Optional[str] = None,
    slot_id: Optional[str] = None
) -> WalletTransaction:
    """
    Transactionally credits a user's wallet with row-level locking (FOR UPDATE).
    Enforces idempotency if reference_id is provided, creates an immutable ledger entry,
    and updates balance atomically.
    """
    if amount <= 0:
        raise InvalidTransactionError("Credit amount must be strictly positive.")

    # 1. Obtain row-level lock on user's wallet
    wallet = get_or_create_wallet(db, user_id, for_update=True)

    # 2. Idempotency Check: Prevent duplicate double-credits for the same reference
    if reference_id:
        existing_txn = db.query(WalletTransaction).filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.category == category,
            WalletTransaction.reference_id == reference_id
        ).first()
        if existing_txn:
            return existing_txn

    # 3. Read current balance AFTER acquiring row lock
    balance_before = wallet.balance
    new_balance = round(balance_before + amount, 2)
    wallet.balance = new_balance
    wallet.total_earned = round(wallet.total_earned + amount, 2)
    balance_after = wallet.balance

    # 4. Create immutable ledger record
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

    # 5. Record audit trail
    log_action(db, 'WALLET_CREDITED', 'Wallet', wallet.id, user_id, {
        'amount': amount,
        'category': category,
        'slot_id': slot_id,
        'reference_id': reference_id,
        'balance_before': balance_before,
        'balance_after': balance_after
    })

    return txn

def debit_wallet(
    db: Session,
    user_id: int,
    amount: float,
    category: str,
    description: str,
    reference_id: Optional[str] = None,
    slot_id: Optional[str] = None
) -> WalletTransaction:
    """
    Transactionally debits a user's wallet with row-level locking (FOR UPDATE).
    Validates available balance post-lock to prevent race conditions and overdrafts.
    """
    if amount <= 0:
        raise InvalidTransactionError("Debit amount must be strictly positive.")

    # 1. Obtain row-level lock on user's wallet
    wallet = get_or_create_wallet(db, user_id, for_update=True)

    # 2. Idempotency Check: Return existing transaction if already executed
    if reference_id:
        existing_txn = db.query(WalletTransaction).filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.category == category,
            WalletTransaction.reference_id == reference_id
        ).first()
        if existing_txn:
            return existing_txn

    # 3. Read current balance AFTER acquiring row lock
    balance_before = wallet.balance
    if balance_before < amount:
        raise InsufficientBalanceError(f"Insufficient wallet balance. Available: ₹{balance_before:,.2f}, Requested: ₹{amount:,.2f}")

    # 4. Mutate balance
    new_balance = round(balance_before - amount, 2)
    wallet.balance = new_balance
    if category == 'WITHDRAWAL':
        wallet.total_withdrawn = round(wallet.total_withdrawn + amount, 2)
    balance_after = wallet.balance

    # 5. Create immutable ledger record
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

    # 6. Record audit trail
    log_action(db, 'WALLET_DEBITED', 'Wallet', wallet.id, user_id, {
        'amount': amount,
        'category': category,
        'slot_id': slot_id,
        'reference_id': reference_id,
        'balance_before': balance_before,
        'balance_after': balance_after
    })

    return txn

def adjust_wallet_balance(
    db: Session,
    user_id: int,
    amount: float,
    admin_id: int,
    reason: str,
    slot_id: Optional[str] = None
) -> WalletTransaction:
    """
    Transactionally adjusts a user's wallet balance (admin override) with row-level locking.
    Prevents adjustments that would result in a negative balance.
    """
    if amount == 0:
        raise InvalidTransactionError("Adjustment amount cannot be zero.")

    # 1. Obtain row-level lock on user's wallet
    wallet = get_or_create_wallet(db, user_id, for_update=True)

    # 2. Read balance AFTER acquiring lock
    balance_before = wallet.balance
    new_balance = round(balance_before + amount, 2)
    if new_balance < 0:
        raise InsufficientBalanceError(f"Adjustment would result in negative balance: ₹{new_balance:,.2f}")

    wallet.balance = new_balance
    if amount > 0:
        wallet.total_earned = round(wallet.total_earned + amount, 2)
    balance_after = wallet.balance

    ref_id = f"ADMIN-ADJ-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # 3. Create ledger entry
    txn = WalletTransaction(
        wallet_id=wallet.id,
        user_id=user_id,
        transaction_type='ADMIN_ADJUSTMENT',
        amount=abs(amount),
        balance_before=balance_before,
        balance_after=balance_after,
        category='ADMIN_ADJUSTMENT',
        slot_id=slot_id,
        reference_id=ref_id,
        description=f"Admin Adjustment: {reason}"
    )
    db.add(txn)
    db.flush()

    # 4. Audit trail
    log_action(db, 'WALLET_ADJUSTED', 'Wallet', wallet.id, admin_id, {
        'adjusted_user_id': user_id,
        'adjustment_amount': amount,
        'reason': reason,
        'slot_id': slot_id,
        'balance_before': balance_before,
        'balance_after': balance_after
    })

    return txn

def create_withdrawal_request(
    db: Session,
    user_id: int,
    amount: float,
    payout_method: str = 'VIRTUAL_UPI',
    payout_details: Optional[Dict[str, Any]] = None
) -> Withdrawal:
    """
    Creates a withdrawal request after locking the user's wallet row and verifying
    that available balance (balance minus all existing PENDING withdrawals) is sufficient.
    """
    if amount <= 0:
        raise InvalidTransactionError("Withdrawal amount must be greater than 0.")

    # 1. Lock wallet row
    wallet = get_or_create_wallet(db, user_id, for_update=True)

    # 2. Calculate existing pending withdrawals
    pending_amount = db.query(func.coalesce(func.sum(Withdrawal.amount), 0.0)).filter(
        Withdrawal.user_id == user_id,
        Withdrawal.status == 'PENDING'
    ).scalar() or 0.0

    available_balance = round(wallet.balance - pending_amount, 2)
    if available_balance < amount:
        raise InsufficientBalanceError(
            f"Cannot request withdrawal of ₹{amount:,.2f}. "
            f"Available balance is ₹{available_balance:,.2f} "
            f"(Total balance: ₹{wallet.balance:,.2f}, Pending requests: ₹{pending_amount:,.2f})."
        )

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
        'code': wdr_code,
        'available_balance_after_request': available_balance - amount
    })
    return withdrawal

def approve_withdrawal(db: Session, withdrawal_id: int, admin_id: int, notes: Optional[str] = None) -> Withdrawal:
    """
    Approves a withdrawal request, debits the user's wallet using FOR UPDATE,
    and updates the withdrawal record to APPROVED atomically.
    """
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).with_for_update().first()
    if not withdrawal:
        raise InvalidTransactionError("Withdrawal record not found.")
    if withdrawal.status != 'PENDING':
        raise InvalidTransactionError(f"Cannot approve withdrawal in '{withdrawal.status}' state.")

    # Debit wallet with row lock & validation
    debit_wallet(
        db,
        user_id=withdrawal.user_id,
        amount=withdrawal.amount,
        category='WITHDRAWAL',
        description=f"Payout for Request {withdrawal.withdrawal_code}",
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

def reject_withdrawal(db: Session, withdrawal_id: int, admin_id: int, notes: Optional[str] = None) -> Withdrawal:
    """
    Rejects a pending withdrawal request.
    """
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).with_for_update().first()
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
