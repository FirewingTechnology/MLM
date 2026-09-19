from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.daily_reward import DailyRewardCycle, DailyRewardTransaction
from app.models.purchase import Purchase
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action
from app.services.time_service import time_provider, IST
from app.services.pair_service import pair_service

class SettlementTimingError(Exception):
    """Raised when settlement is attempted before 07:00 AM IST for today."""
    pass

class DailyRewardService:
    BASE_DAILY_REWARD = 50.0
    PAIR_INCREMENT = 50.0
    DEFAULT_REFUND_TARGET = 35400.0

    @classmethod
    def calculate_current_daily_reward(cls, completed_pairs: int) -> float:
        """
        Formula:
        current_daily_reward = ₹50 + (completed_pairs × ₹50)
        Examples:
        0 completed pairs = ₹50/day
        1 completed pair   = ₹100/day
        2 completed pairs  = ₹150/day
        3 completed pairs  = ₹200/day
        4 completed pairs  = ₹250/day
        """
        return cls.BASE_DAILY_REWARD + (max(0, completed_pairs) * cls.PAIR_INCREMENT)

    @classmethod
    def create_daily_reward_cycle(cls, db: Session, purchase_id: int) -> DailyRewardCycle:
        """
        Creates an independent Daily Package Refund Cycle for a qualifying purchase.
        Idempotent: returns existing cycle if already created for this purchase.
        """
        # 1. Check if cycle already exists for this purchase
        existing = db.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase_id).first()
        if existing:
            return existing

        purchase = db.get(Purchase, purchase_id)
        if not purchase:
            raise ValueError(f"Purchase with id {purchase_id} not found.")

        current_ist = time_provider.get_current_ist_time(db)
        completed_pairs = pair_service.get_completed_pair_count(db, purchase.user_id)
        current_reward = cls.calculate_current_daily_reward(completed_pairs)
        refund_target = purchase.amount or cls.DEFAULT_REFUND_TARGET

        cycle = DailyRewardCycle(
            purchase_id=purchase.id,
            user_id=purchase.user_id,
            package_id=purchase.package_id,
            refund_target=refund_target,
            refunded_amount=0.0,
            completed_pairs=completed_pairs,
            base_daily_amount=cls.BASE_DAILY_REWARD,
            pair_increment=cls.PAIR_INCREMENT,
            current_daily_reward=current_reward,
            status='ACTIVE',
            last_credit_date=None,
            started_at=current_ist.replace(tzinfo=None),
            created_at=current_ist.replace(tzinfo=None),
            updated_at=current_ist.replace(tzinfo=None)
        )
        db.add(cycle)
        db.flush()

        log_action(db, 'DAILY_REWARD_CYCLE_CREATED', 'DailyRewardCycle', cycle.id, purchase.user_id, {
            'purchase_id': purchase.id,
            'refund_target': refund_target,
            'completed_pairs': completed_pairs,
            'initial_daily_reward': current_reward
        })

        return cycle

    @classmethod
    def get_completed_pair_count(cls, db: Session, user_id: int) -> int:
        """
        Calculated strictly from the authoritative pairing/settlement engine.
        Does NOT count referrals, registrations, placements, or incomplete pairs.
        """
        return pair_service.get_completed_pair_count(db, user_id)

    @classmethod
    def get_current_daily_reward(cls, db: Session, user_id: int, cycle_id: Optional[int] = None) -> float:
        completed_pairs = cls.get_completed_pair_count(db, user_id)
        return cls.calculate_current_daily_reward(completed_pairs)

    @classmethod
    def settle_user_daily_reward(
        cls,
        db: Session,
        cycle_id: int,
        business_date_str: str,
        current_ist: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Settles a single user's daily reward cycle for the specified business date.
        Uses row-level locking (with_for_update) and idempotency checks.
        """
        cycle = db.query(DailyRewardCycle).filter(DailyRewardCycle.id == cycle_id).with_for_update().first()
        if not cycle or cycle.status != 'ACTIVE':
            return None

        # Idempotency check 1: Cycle last_credit_date
        if cycle.last_credit_date == business_date_str:
            return {'status': 'SKIPPED_ALREADY_CREDITED', 'cycle_id': cycle.id, 'user_id': cycle.user_id}

        idempotency_key = f"DAILY_REFUND:{cycle.purchase_id}:{business_date_str}"

        # Idempotency check 2: Existing DailyRewardTransaction
        existing_txn = db.query(DailyRewardTransaction).filter(
            DailyRewardTransaction.idempotency_key == idempotency_key
        ).first()
        if existing_txn:
            cycle.last_credit_date = business_date_str
            db.flush()
            return {'status': 'SKIPPED_ALREADY_CREDITED', 'cycle_id': cycle.id, 'user_id': cycle.user_id}

        # Check remaining capacity
        remaining_refund = round(cycle.refund_target - cycle.refunded_amount, 2)
        if remaining_refund <= 0:
            cycle.status = 'COMPLETED'
            cycle.completed_at = current_ist.replace(tzinfo=None)
            cycle.updated_at = current_ist.replace(tzinfo=None)
            db.flush()
            return {'status': 'SKIPPED_COMPLETED', 'cycle_id': cycle.id, 'user_id': cycle.user_id}

        # Fetch actual completed pairs from authoritative pairing engine
        completed_pairs = cls.get_completed_pair_count(db, cycle.user_id)
        current_daily_reward = cls.calculate_current_daily_reward(completed_pairs)

        # Daily credit is MIN(current_daily_reward, remaining_refund)
        daily_credit = min(current_daily_reward, remaining_refund)
        daily_credit = round(daily_credit, 2)

        if daily_credit <= 0:
            return {'status': 'SKIPPED_ZERO_AMOUNT', 'cycle_id': cycle.id, 'user_id': cycle.user_id}

        purchase_code = cycle.purchase.purchase_code if cycle.purchase else f"PUR-{cycle.purchase_id}"
        description = f"Daily Package Refund for {purchase_code} ({business_date_str}) - Pairs: {completed_pairs}"

        # Credit wallet under dedicated category DAILY_PACKAGE_REFUND
        # credit_wallet itself acquires row-lock and checks reference_id idempotency
        wallet_txn = credit_wallet(
            db=db,
            user_id=cycle.user_id,
            amount=daily_credit,
            category='DAILY_PACKAGE_REFUND',
            description=description,
            reference_id=idempotency_key
        )

        # Create immutable daily reward transaction record
        dr_txn = DailyRewardTransaction(
            cycle_id=cycle.id,
            purchase_id=cycle.purchase_id,
            user_id=cycle.user_id,
            business_date=business_date_str,
            amount=daily_credit,
            completed_pairs_snapshot=completed_pairs,
            daily_reward_snapshot=current_daily_reward,
            wallet_transaction_id=wallet_txn.id if wallet_txn else None,
            idempotency_key=idempotency_key,
            description=description,
            created_at=current_ist.replace(tzinfo=None)
        )
        db.add(dr_txn)

        # Mutate cycle state
        cycle.refunded_amount = round(cycle.refunded_amount + daily_credit, 2)
        cycle.completed_pairs = completed_pairs
        cycle.current_daily_reward = current_daily_reward
        cycle.last_credit_date = business_date_str
        cycle.updated_at = current_ist.replace(tzinfo=None)

        if cycle.refunded_amount >= cycle.refund_target:
            cycle.status = 'COMPLETED'
            cycle.completed_at = current_ist.replace(tzinfo=None)

        db.flush()

        log_action(db, 'DAILY_REWARD_CREDITED', 'DailyRewardCycle', cycle.id, cycle.user_id, {
            'business_date': business_date_str,
            'amount': daily_credit,
            'completed_pairs': completed_pairs,
            'current_daily_reward': current_daily_reward,
            'refunded_amount': cycle.refunded_amount,
            'remaining_refund': cycle.remaining_refund,
            'cycle_status': cycle.status,
            'idempotency_key': idempotency_key
        })

        return {
            'status': 'CREDITED',
            'cycle_id': cycle.id,
            'user_id': cycle.user_id,
            'amount': daily_credit,
            'completed_pairs': completed_pairs,
            'remaining_refund': cycle.remaining_refund,
            'cycle_status': cycle.status
        }

    @classmethod
    def settle_daily_rewards(
        cls,
        db: Session,
        business_date: Optional[date] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Executes daily settlement for all active DailyRewardCycles.
        Strictly enforces:
        1. 07:00 AM IST cutoff (settlement for today cannot run before 07:00 AM IST).
        2. Idempotency: each cycle is credited at most once per business date.
        3. Transactional row locking.
        """
        current_ist = time_provider.get_current_ist_time(db)
        today_ist_date = current_ist.date()
        target_date = business_date or today_ist_date
        target_date_str = target_date.strftime('%Y-%m-%d')

        # If settling for today or future, enforce 07:00 AM IST cutoff
        if not force and target_date >= today_ist_date:
            cutoff_time = time(7, 0, 0)
            if current_ist.time() < cutoff_time:
                raise SettlementTimingError(
                    f"Daily refund settlement for {target_date_str} cannot be executed before 07:00 AM IST. "
                    f"Current IST time is {current_ist.strftime('%I:%M:%S %p')}."
                )

        # Find all active cycles
        active_cycles = db.query(DailyRewardCycle).filter(
            DailyRewardCycle.status == 'ACTIVE'
        ).order_by(DailyRewardCycle.id.asc()).all()

        total_processed = 0
        credited_count = 0
        skipped_count = 0
        total_credited_amount = 0.0
        results = []

        for cycle in active_cycles:
            try:
                # Use subtransaction/savepoint per user cycle to prevent one error from breaking whole batch
                with db.begin_nested():
                    res = cls.settle_user_daily_reward(
                        db=db,
                        cycle_id=cycle.id,
                        business_date_str=target_date_str,
                        current_ist=current_ist
                    )
                    if res:
                        total_processed += 1
                        if res['status'] == 'CREDITED':
                            credited_count += 1
                            total_credited_amount = round(total_credited_amount + res['amount'], 2)
                        else:
                            skipped_count += 1
                        results.append(res)
            except Exception as e:
                skipped_count += 1
                results.append({
                    'status': 'ERROR',
                    'cycle_id': cycle.id,
                    'user_id': cycle.user_id,
                    'error': str(e)
                })

        db.flush()

        return {
            'business_date': target_date_str,
            'settlement_time': current_ist.isoformat(),
            'total_active_cycles': len(active_cycles),
            'processed_count': total_processed,
            'credited_count': credited_count,
            'skipped_count': skipped_count,
            'total_credited_amount': total_credited_amount,
            'results': results
        }

    @classmethod
    def get_user_daily_reward_overview(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Returns overview data for the user dashboard.
        """
        current_ist = time_provider.get_current_ist_time(db)
        active_cycle = db.query(DailyRewardCycle).filter(
            DailyRewardCycle.user_id == user_id,
            DailyRewardCycle.status == 'ACTIVE'
        ).order_by(DailyRewardCycle.id.desc()).first()

        completed_pairs = cls.get_completed_pair_count(db, user_id)
        current_daily_reward = cls.calculate_current_daily_reward(completed_pairs)

        # Look up most recent cycle if no active cycle
        latest_cycle = active_cycle or db.query(DailyRewardCycle).filter(
            DailyRewardCycle.user_id == user_id
        ).order_by(DailyRewardCycle.id.desc()).first()

        # Next credit time: 07:00 AM IST today if before 7 AM, else 07:00 AM IST tomorrow
        today_date = current_ist.date()
        if current_ist.time() < time(7, 0, 0):
            next_credit_dt = datetime.combine(today_date, time(7, 0, 0), tzinfo=IST)
        else:
            next_credit_dt = datetime.combine(today_date + timedelta(days=1), time(7, 0, 0), tzinfo=IST)

        # Recent transactions
        recent_txns = db.query(DailyRewardTransaction).filter(
            DailyRewardTransaction.user_id == user_id
        ).order_by(DailyRewardTransaction.id.desc()).limit(10).all()

        total_refunded_all_time = db.query(
            func.coalesce(func.sum(DailyRewardTransaction.amount), 0.0)
        ).filter(DailyRewardTransaction.user_id == user_id).scalar() or 0.0

        cycle_dict = None
        if latest_cycle:
            cycle_dict = latest_cycle.to_dict()
            # Update dynamic completed pairs and reward in response
            cycle_dict['completed_pairs'] = completed_pairs
            cycle_dict['current_daily_reward'] = current_daily_reward

        return {
            'has_active_cycle': active_cycle is not None,
            'cycle': cycle_dict,
            'completed_pairs': completed_pairs,
            'current_daily_reward': current_daily_reward,
            'total_refunded': total_refunded_all_time,
            'next_credit_time': next_credit_dt.isoformat(),
            'next_credit_time_formatted': "07:00 AM IST",
            'recent_transactions': [t.to_dict() for t in recent_txns]
        }

    @classmethod
    def get_admin_daily_reward_cycles(
        cls,
        db: Session,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Admin endpoint to list, filter, and paginate daily reward cycles with summary KPIs.
        """
        query = db.query(DailyRewardCycle).join(User, DailyRewardCycle.user_id == User.id)

        if status_filter and status_filter.upper() != 'ALL':
            query = query.filter(DailyRewardCycle.status == status_filter.upper())

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(term),
                    User.user_code.ilike(term),
                    User.email.ilike(term)
                )
            )

        total_count = query.count()
        cycles = query.order_by(DailyRewardCycle.id.desc()).offset(offset).limit(limit).all()

        # Summary KPIs
        total_active = db.query(DailyRewardCycle).filter(DailyRewardCycle.status == 'ACTIVE').count()
        total_completed = db.query(DailyRewardCycle).filter(DailyRewardCycle.status == 'COMPLETED').count()
        total_refunded_sum = db.query(
            func.coalesce(func.sum(DailyRewardCycle.refunded_amount), 0.0)
        ).scalar() or 0.0

        current_ist = time_provider.get_current_ist_time(db)
        today_str = current_ist.strftime('%Y-%m-%d')
        today_credited = db.query(
            func.coalesce(func.sum(DailyRewardTransaction.amount), 0.0)
        ).filter(DailyRewardTransaction.business_date == today_str).scalar() or 0.0

        return {
            'items': [c.to_dict() for c in cycles],
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'summary': {
                'total_cycles': total_active + total_completed,
                'active_cycles': total_active,
                'completed_cycles': total_completed,
                'total_refunded_all_time': total_refunded_sum,
                'today_credited_amount': today_credited,
                'today_business_date': today_str
            }
        }

    @classmethod
    def get_admin_daily_reward_transactions(
        cls,
        db: Session,
        cycle_id: Optional[int] = None,
        user_id: Optional[int] = None,
        business_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Admin endpoint to list and audit settlement transactions.
        """
        query = db.query(DailyRewardTransaction)
        if cycle_id:
            query = query.filter(DailyRewardTransaction.cycle_id == cycle_id)
        if user_id:
            query = query.filter(DailyRewardTransaction.user_id == user_id)
        if business_date:
            query = query.filter(DailyRewardTransaction.business_date == business_date)

        total_count = query.count()
        txns = query.order_by(DailyRewardTransaction.id.desc()).offset(offset).limit(limit).all()

        return {
            'items': [t.to_dict() for t in txns],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

daily_reward_service = DailyRewardService()
