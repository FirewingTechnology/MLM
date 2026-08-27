from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.models.user import User
from app.models.period_volume import BinaryPeriodVolume
from app.models.volume import BinaryVolume
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.commission import Commission
from app.models.pair_event import PairEvent
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action
from app.services.mlm_service import is_binary_qualified, get_leg_subtree_user_ids

class PairBonusService:
    @staticmethod
    def get_or_create_period_volume(db: Session, user_id: int, slot_id: str) -> BinaryPeriodVolume:
        """
        Retrieves the BinaryPeriodVolume for the specified user and slot_id.
        If it does not exist, creates it initializing starting carry-forward from
        the previous period's ending carry-forward (or legacy BinaryVolume).
        """
        period_vol = db.query(BinaryPeriodVolume).filter(
            BinaryPeriodVolume.user_id == user_id,
            BinaryPeriodVolume.slot_id == slot_id
        ).first()

        if period_vol:
            return period_vol

        # Look up most recent prior period volume for this user
        prior_vol = db.query(BinaryPeriodVolume).filter(
            BinaryPeriodVolume.user_id == user_id
        ).order_by(BinaryPeriodVolume.id.desc()).first()

        if prior_vol:
            starting_carry_left = prior_vol.ending_carry_left
            starting_carry_right = prior_vol.ending_carry_right
        else:
            # Fallback to base BinaryVolume carry if any
            legacy_vol = db.query(BinaryVolume).filter(BinaryVolume.user_id == user_id).first()
            starting_carry_left = legacy_vol.carry_left_bv if legacy_vol else 0.0
            starting_carry_right = legacy_vol.carry_right_bv if legacy_vol else 0.0

        period_vol = BinaryPeriodVolume(
            user_id=user_id,
            slot_id=slot_id,
            starting_carry_left=starting_carry_left,
            starting_carry_right=starting_carry_right,
            current_left_bv=0.0,
            current_right_bv=0.0,
            effective_left_bv=starting_carry_left,
            effective_right_bv=starting_carry_right,
            pair_completed=False,
            pair_bonus=0.0,
            consumed_left_bv=0.0,
            consumed_right_bv=0.0,
            ending_carry_left=starting_carry_left,
            ending_carry_right=starting_carry_right
        )
        db.add(period_vol)
        db.flush()
        return period_vol

    @staticmethod
    def consume_ancestor_volume_ledger(db: Session, ancestor_user_id: int, side: str, amount_to_consume: float):
        """
        Consumes exact volume from the ancestor's active VolumeLedger entries in FIFO order.
        """
        entries = db.query(VolumeLedger).filter(
            VolumeLedger.ancestor_user_id == ancestor_user_id,
            VolumeLedger.side == side,
            VolumeLedger.remaining_amount > 0
        ).order_by(VolumeLedger.id.asc()).all()

        rem_to_consume = amount_to_consume
        for entry in entries:
            if rem_to_consume <= 0:
                break
            consumed = min(entry.remaining_amount, rem_to_consume)
            entry.consumed_amount += consumed
            entry.remaining_amount -= consumed
            rem_to_consume -= consumed
            if entry.remaining_amount <= 0.0001:
                entry.status = 'CONSUMED'
                entry.remaining_amount = 0.0
        db.flush()

    @staticmethod
    def record_slot_settlement(
        db: Session,
        user_id: int,
        slot_id: str,
        created_at: Optional[datetime] = None
    ) -> SlotSettlement:
        """
        Records or updates an idempotent SlotSettlement record for the user and slot.
        """
        period_vol = PairBonusService.get_or_create_period_volume(db, user_id, slot_id)
        
        carry_comm_earned = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).filter(
            Commission.beneficiary_id == user_id,
            Commission.commission_type == 'CARRY_COMMISSION',
            Commission.slot_id == slot_id
        ).scalar() or 0.0

        matching_comm_earned = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).filter(
            Commission.beneficiary_id == user_id,
            Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING']),
            Commission.slot_id == slot_id
        ).scalar() or 0.0

        settlement = db.query(SlotSettlement).filter(
            SlotSettlement.user_id == user_id,
            SlotSettlement.slot_id == slot_id
        ).first()

        now_dt = created_at or datetime.utcnow()
        if not settlement:
            settlement = SlotSettlement(
                user_id=user_id,
                slot_id=slot_id,
                left_before=period_vol.effective_left_bv,
                right_before=period_vol.effective_right_bv,
                left_matched=period_vol.consumed_left_bv,
                right_matched=period_vol.consumed_right_bv,
                pairs_paid=1 if period_vol.pair_completed else 0,
                pair_bonus=period_vol.pair_bonus,
                left_carry=period_vol.ending_carry_left,
                right_carry=period_vol.ending_carry_right,
                carry_commission=carry_comm_earned,
                matching_commission=matching_comm_earned,
                status='SETTLED',
                processed_at=now_dt,
                created_at=now_dt,
                updated_at=now_dt
            )
            db.add(settlement)
        else:
            settlement.left_before = period_vol.effective_left_bv
            settlement.right_before = period_vol.effective_right_bv
            settlement.left_matched = period_vol.consumed_left_bv
            settlement.right_matched = period_vol.consumed_right_bv
            settlement.pairs_paid = 1 if period_vol.pair_completed else 0
            settlement.pair_bonus = period_vol.pair_bonus
            settlement.left_carry = period_vol.ending_carry_left
            settlement.right_carry = period_vol.ending_carry_right
            settlement.carry_commission = carry_comm_earned
            settlement.matching_commission = matching_comm_earned
            settlement.updated_at = now_dt

        db.flush()
        return settlement

    @staticmethod
    def record_bv_and_evaluate_pairs(
        db: Session,
        user_id: int,
        leg: str,
        bv_amount: float,
        slot_id: str,
        purchase_id: Optional[int] = None,
        source_user_id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ) -> Optional[dict]:
        """
        Records new BV on a specific leg (LEFT or RIGHT) within the current slot,
        recalculates effective and carry-forward volumes, and evaluates pair completion.
        """
        period_vol = PairBonusService.get_or_create_period_volume(db, user_id, slot_id)

        if leg.upper() == 'LEFT':
            period_vol.current_left_bv += bv_amount
        elif leg.upper() == 'RIGHT':
            period_vol.current_right_bv += bv_amount

        # Update effective BV
        period_vol.effective_left_bv = period_vol.starting_carry_left + period_vol.current_left_bv
        period_vol.effective_right_bv = period_vol.starting_carry_right + period_vol.current_right_bv

        # Update ending carry based on current consumption
        period_vol.ending_carry_left = period_vol.effective_left_bv - period_vol.consumed_left_bv
        period_vol.ending_carry_right = period_vol.effective_right_bv - period_vol.consumed_right_bv
        db.flush()

        # Record settlement state
        PairBonusService.record_slot_settlement(db, user_id, slot_id, created_at)

        # Evaluate pair qualification
        return PairBonusService.evaluate_and_award_pair(
            db=db,
            user_id=user_id,
            slot_id=slot_id,
            purchase_id=purchase_id,
            source_user_id=source_user_id,
            created_at=created_at
        )

    @staticmethod
    def evaluate_and_award_pair(
        db: Session,
        user_id: int,
        slot_id: str,
        purchase_id: Optional[int] = None,
        source_user_id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ) -> Optional[dict]:
        """
        Evaluates whether a 30k/30k pair is formed for the given user in slot_id.
        If pair forms and has not yet been paid for this slot (max 1 pair/slot),
        consumes 30k/30k from period and volume ledger, records PAIR_BONUS Commission (₹15,000),
        awards configured Matching Commission (10% = ₹1,500) to eligible sponsor, and records SlotSettlement.
        """
        period_vol = PairBonusService.get_or_create_period_volume(db, user_id, slot_id)

        # If already completed in this slot, no more pair bonuses are awarded
        if period_vol.pair_completed:
            return None

        # Check DB uniqueness / existing commission for idempotency
        existing_comm = db.query(Commission).filter(
            Commission.beneficiary_id == user_id,
            Commission.commission_type == 'PAIR_BONUS',
            Commission.slot_id == slot_id
        ).first()

        if existing_comm:
            period_vol.pair_completed = True
            period_vol.pair_bonus = existing_comm.amount
            db.flush()
            PairBonusService.record_slot_settlement(db, user_id, slot_id, created_at)
            return None

        qualifying_bv = settings.PAIR_VOLUME  # 30,000
        bonus_amount = settings.PAIR_BONUS   # 15,000

        eligible_left_pairs = int(period_vol.effective_left_bv // qualifying_bv)
        eligible_right_pairs = int(period_vol.effective_right_bv // qualifying_bv)
        possible_pairs = min(eligible_left_pairs, eligible_right_pairs)

        if possible_pairs < 1:
            PairBonusService.record_slot_settlement(db, user_id, slot_id, created_at)
            return None

        # CRITICAL MLM QUALIFICATION RULE:
        # A user ONLY qualifies for a ₹15,000 Pair Bonus if they are active AND Binary Qualified
        # (personally sponsored at least 1 active member in their LEFT leg AND 1 active member in their RIGHT leg).
        # Placement parents (like Kumar) who merely receive spillover volume do NOT earn Pair Bonuses.
        if not is_binary_qualified(db, user_id):
            PairBonusService.record_slot_settlement(db, user_id, slot_id, created_at)
            return None

        # Exactly 1 pair is paid per slot
        period_vol.consumed_left_bv = qualifying_bv
        period_vol.consumed_right_bv = qualifying_bv
        period_vol.ending_carry_left = period_vol.effective_left_bv - qualifying_bv
        period_vol.ending_carry_right = period_vol.effective_right_bv - qualifying_bv
        period_vol.pair_completed = True
        period_vol.pair_bonus = bonus_amount
        db.flush()

        # Consume VolumeLedger entries for this user
        PairBonusService.consume_ancestor_volume_ledger(db, user_id, 'LEFT', qualifying_bv)
        PairBonusService.consume_ancestor_volume_ledger(db, user_id, 'RIGHT', qualifying_bv)

        user = db.get(User, user_id)

        # 0. Find representative lineage sources and record explicit PairEvent
        left_sub = get_leg_subtree_user_ids(db, user_id, 'LEFT')
        right_sub = get_leg_subtree_user_ids(db, user_id, 'RIGHT')
        
        left_direct = db.query(User).filter(
            User.sponsor_id == user_id,
            User.id.in_(left_sub),
            User.is_active == True
        ).first()
        right_direct = db.query(User).filter(
            User.sponsor_id == user_id,
            User.id.in_(right_sub),
            User.is_active == True
        ).first()

        pair_event_record = PairEvent(
            pair_earner_user_id=user_id,
            slot_id=slot_id,
            purchase_id=purchase_id,
            left_source_user_id=left_direct.id if left_direct else (source_user_id if source_user_id in left_sub else None),
            right_source_user_id=right_direct.id if right_direct else (source_user_id if source_user_id in right_sub else None),
            matched_left_bv=qualifying_bv,
            matched_right_bv=qualifying_bv,
            pair_bonus=bonus_amount,
            matching_upline_id=user.sponsor_id if user else None,
            matching_commission=0.0,
            status='COMPLETED',
            idempotency_key=f"PAIR-EVENT-{slot_id}-{user_id}",
            created_at=created_at or datetime.utcnow()
        )
        db.add(pair_event_record)
        db.flush()

        # 1. Record Pair Bonus Commission & Credit User Wallet
        calc_details = {
            'trigger': 'PAIR_BONUS',
            'pair_event_id': pair_event_record.id,
            'slot_id': slot_id,
            'qualifying_bv': qualifying_bv,
            'pair_bonus_amount': bonus_amount,
            'effective_left_bv': period_vol.effective_left_bv,
            'effective_right_bv': period_vol.effective_right_bv,
            'consumed_left_bv': period_vol.consumed_left_bv,
            'consumed_right_bv': period_vol.consumed_right_bv,
            'ending_carry_left': period_vol.ending_carry_left,
            'ending_carry_right': period_vol.ending_carry_right,
            'explanation': (
                f"Binary Pair Bonus of ₹{bonus_amount:,.0f} awarded for matching 30,000 BV on Left & Right. "
                f"Ending Carry Forward: Left: ₹{period_vol.ending_carry_left:,.0f} BV, "
                f"Right: ₹{period_vol.ending_carry_right:,.0f} BV (Slot: {slot_id})."
            )
        }

        comm = Commission(
            beneficiary_id=user_id,
            source_user_id=source_user_id,
            purchase_id=purchase_id,
            commission_type='PAIR_BONUS',
            slot_id=slot_id,
            amount=bonus_amount,
            bv_basis=qualifying_bv,
            percentage=(bonus_amount / qualifying_bv) * 100.0,
            created_at=created_at or datetime.utcnow(),
            _calculation_details=None
        )
        comm.calculation_details = calc_details
        db.add(comm)
        db.flush()

        credit_wallet(
            db,
            user_id=user_id,
            amount=bonus_amount,
            category='PAIR_BONUS',
            description=f"Binary Pair Bonus (30k/30k match) [{slot_id}]",
            reference_id=f"PAIR-{slot_id}-{user_id}",
            slot_id=slot_id
        )

        log_action(db, 'PAIR_BONUS_AWARDED', 'Commission', comm.id, user_id, {
            'slot_id': slot_id,
            'amount': bonus_amount,
            'pair_event_id': pair_event_record.id,
            'ending_carry_left': period_vol.ending_carry_left,
            'ending_carry_right': period_vol.ending_carry_right
        })

        # 2. Process Matching / Upline Commission to user's direct sponsor
        matching_event = None
        if (settings.MATCHING_COMMISSION_ENABLED or settings.CARRY_COMMISSION_ENABLED) and user and user.sponsor_id:
            sponsor = db.get(User, user.sponsor_id)
            if sponsor:
                # Idempotency check: ensure no duplicate matching commission for same slot + child pair
                existing_matching = db.query(Commission).filter(
                    Commission.beneficiary_id == sponsor.id,
                    Commission.source_user_id == user.id,
                    Commission.commission_type.in_(['MATCHING_COMMISSION', 'CARRY_COMMISSION']),
                    Commission.slot_id == slot_id
                ).first()

                if not existing_matching:
                    base_option = (getattr(settings, 'MATCHING_COMMISSION_BASE', None) or getattr(settings, 'CARRY_COMMISSION_BASE', None) or "PAIR_BONUS").upper()
                    if base_option == "MATCHED_BV":
                        base_amount = qualifying_bv
                    elif base_option == "PAIR_VOLUME":
                        base_amount = settings.PAIR_VOLUME
                    else:  # PAIR_BONUS
                        base_amount = bonus_amount

                    rate = getattr(settings, 'MATCHING_COMMISSION_RATE', None) or getattr(settings, 'CARRY_COMMISSION_RATE', 0.10)
                    matching_bonus = base_amount * rate

                    calc_details_matching = {
                        'trigger': 'MATCHING_COMMISSION',
                        'slot_id': slot_id,
                        'source_user': {'id': user.id, 'name': user.full_name, 'code': user.user_code},
                        'pair_commission_id': comm.id,
                        'rate': rate * 100.0,
                        'base_type': base_option,
                        'base_amount': base_amount,
                        'earned_amount': matching_bonus,
                        'explanation': (
                            f"{rate * 100:.0f}% Matching Commission of ₹{matching_bonus:,.0f} from {user.full_name}'s "
                            f"Pair Bonus of ₹{bonus_amount:,.0f} (Base: {base_option}, Slot: {slot_id})."
                        )
                    }

                    matching_comm = Commission(
                        beneficiary_id=sponsor.id,
                        source_user_id=user.id,
                        purchase_id=purchase_id,
                        commission_type='MATCHING_COMMISSION',
                        slot_id=slot_id,
                        amount=matching_bonus,
                        bv_basis=base_amount,
                        percentage=rate * 100.0,
                        created_at=created_at or datetime.utcnow(),
                        _calculation_details=None
                    )
                    matching_comm.calculation_details = calc_details_matching
                    db.add(matching_comm)
                    pair_event_record.matching_commission = matching_bonus
                    db.flush()

                    credit_wallet(
                        db,
                        user_id=sponsor.id,
                        amount=matching_bonus,
                        category='MATCHING_COMMISSION',
                        description=f"Matching Commission ({rate * 100:.0f}%) from {user.full_name} [{slot_id}]",
                        reference_id=f"MATCH-{slot_id}-{sponsor.id}-{user.id}",
                        slot_id=slot_id
                    )

                    log_action(db, 'MATCHING_COMMISSION_AWARDED', 'Commission', matching_comm.id, sponsor.id, {
                        'slot_id': slot_id,
                        'source_user_id': user.id,
                        'amount': matching_bonus
                    })

                    matching_event = {
                        'type': 'MATCHING_COMMISSION',
                        'beneficiary_id': sponsor.id,
                        'beneficiary_name': sponsor.full_name,
                        'source_user_id': user.id,
                        'source_user_name': user.full_name,
                        'amount': matching_bonus,
                        'slot_id': slot_id
                    }

                    # Update sponsor's settlement record to reflect matching commission
                    PairBonusService.record_slot_settlement(db, sponsor.id, slot_id, created_at)

        # Update settlement for this user
        PairBonusService.record_slot_settlement(db, user_id, slot_id, created_at)

        result = {
            'type': 'PAIR_BONUS',
            'beneficiary_id': user_id,
            'beneficiary_name': user.full_name if user else '',
            'amount': bonus_amount,
            'slot_id': slot_id,
            'ending_carry_left': period_vol.ending_carry_left,
            'ending_carry_right': period_vol.ending_carry_right
        }
        if matching_event:
            result['matching_commission_event'] = matching_event
            result['carry_commission_event'] = matching_event

        return result

    @staticmethod
    def get_user_pair_summary(db: Session, user_id: int, slot_id: str) -> dict:
        """
        Returns structured pair volume and status summary for user in given slot.
        """
        period_vol = PairBonusService.get_or_create_period_volume(db, user_id, slot_id)
        qualifying_bv = settings.PAIR_VOLUME
        bonus_amount = settings.PAIR_BONUS

        needed_left = max(0.0, qualifying_bv - period_vol.effective_left_bv)
        needed_right = max(0.0, qualifying_bv - period_vol.effective_right_bv)

        carry_comm_earned = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).filter(
            Commission.beneficiary_id == user_id,
            Commission.commission_type == 'CARRY_COMMISSION',
            Commission.slot_id == slot_id
        ).scalar() or 0.0

        matching_comm_earned = db.query(func.coalesce(func.sum(Commission.amount), 0.0)).filter(
            Commission.beneficiary_id == user_id,
            Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING']),
            Commission.slot_id == slot_id
        ).scalar() or 0.0

        return {
            'pair_volume_threshold': qualifying_bv,
            'pair_bonus_amount': bonus_amount,
            'max_pairs_per_period': settings.MAX_PAIRS_PER_SLOT,
            'slot_id': slot_id,
            'current_left_bv': period_vol.current_left_bv,
            'current_right_bv': period_vol.current_right_bv,
            'carry_forward_left': period_vol.starting_carry_left,
            'carry_forward_right': period_vol.starting_carry_right,
            'effective_left_bv': period_vol.effective_left_bv,
            'effective_right_bv': period_vol.effective_right_bv,
            'consumed_left_bv': period_vol.consumed_left_bv,
            'consumed_right_bv': period_vol.consumed_right_bv,
            'ending_carry_left': period_vol.ending_carry_left,
            'ending_carry_right': period_vol.ending_carry_right,
            'pair_completed': period_vol.pair_completed,
            'pair_bonus_earned': period_vol.pair_bonus,
            'matching_commission_earned': matching_comm_earned,
            'carry_commission_earned': carry_comm_earned or matching_comm_earned,
            'needed_left_bv': needed_left,
            'needed_right_bv': needed_right
        }

pair_service = PairBonusService()
