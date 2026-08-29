import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from collections import deque

from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.activation_request import PackageActivationRequest
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_upline_request import SecurityPinUplineRequest
from app.models.pin_ledger import SecurityPinLedger
from app.services.commission_service import process_package_purchase
from app.services.audit_service import log_action

class PinSecurityError(Exception):
    pass

class PinValidationError(Exception):
    pass

class PinService:
    @staticmethod
    def generate_secure_pin() -> Tuple[str, str, str]:
        """
        Generates:
        1. pin_code: Public identifier, e.g. SPIN-ABCD1234
        2. raw_pin: Secret 8-character uppercase alphanumeric code, e.g. 7K9M2X4W
        3. pin_hash: SHA-256 hash of raw_pin
        """
        # Exclude confusing characters like 0, O, 1, I
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        raw_pin = ''.join(secrets.choice(alphabet) for _ in range(8))
        pin_code = f"SPIN-{secrets.token_hex(3).upper()}"
        pin_hash = hashlib.sha256(raw_pin.encode('utf-8')).hexdigest()
        return pin_code, raw_pin, pin_hash

    @staticmethod
    def is_user_in_downline(db: Session, ancestor_id: int, descendant_id: int) -> bool:
        """
        Checks if descendant_id is in the downline of ancestor_id
        via binary placement tree OR sponsor tree.
        """
        if ancestor_id == descendant_id:
            return True
            
        # Check binary tree downline
        visited = set()
        queue = deque([ancestor_id])
        while queue:
            curr_id = queue.popleft()
            if curr_id in visited:
                continue
            visited.add(curr_id)
            if curr_id == descendant_id:
                return True
            children = db.query(User.id).filter(User.binary_parent_id == curr_id).all()
            for (c_id,) in children:
                if c_id not in visited:
                    queue.append(c_id)

        # Check sponsor tree downline
        visited_sponsor = set()
        queue_sponsor = deque([ancestor_id])
        while queue_sponsor:
            curr_id = queue_sponsor.popleft()
            if curr_id in visited_sponsor:
                continue
            visited_sponsor.add(curr_id)
            if curr_id == descendant_id:
                return True
            direct_sponsorees = db.query(User.id).filter(User.sponsor_id == curr_id).all()
            for (s_id,) in direct_sponsorees:
                if s_id not in visited_sponsor:
                    queue_sponsor.append(s_id)

        return False

    @staticmethod
    def get_eligible_downlines(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Returns list of eligible downline members for PIN transfers."""
        eligible_ids = set()
        
        # 1. Binary subtree
        queue = deque([user_id])
        while queue:
            curr = queue.popleft()
            children = db.query(User).filter(User.binary_parent_id == curr).all()
            for child in children:
                eligible_ids.add(child.id)
                queue.append(child.id)

        # 2. Sponsor tree
        queue_sp = deque([user_id])
        while queue_sp:
            curr = queue_sp.popleft()
            directs = db.query(User).filter(User.sponsor_id == curr).all()
            for d in directs:
                eligible_ids.add(d.id)
                queue_sp.append(d.id)

        if not eligible_ids:
            return []

        users = db.query(User).filter(User.id.in_(eligible_ids)).all()
        return [
            {
                'id': u.id,
                'user_code': u.user_code,
                'full_name': u.full_name,
                'email': u.email,
                'is_active': u.is_active,
                'binary_position': u.binary_position,
                'sponsor_id': u.sponsor_id
            }
            for u in users
        ]

    # =========================================================================
    # 1. BULK PREPAID PIN ORDERS (ADMIN PURCHASE)
    # =========================================================================

    @staticmethod
    def create_pin_order(
        db: Session,
        user_id: int,
        package_id: Optional[int] = 1,
        quantity: int = 1,
        payment_method: str = "UPI_TRANSFER",
        payment_reference: str = "",
        payment_proof_url: Optional[str] = None
    ) -> SecurityPinOrder:
        user = db.get(User, user_id)
        if not user:
            raise PinValidationError("User not found.")

        if quantity < 1 or quantity > 500:
            raise PinValidationError("Quantity must be between 1 and 500 PINs.")

        package = db.get(Package, package_id) or db.query(Package).filter(Package.is_active == True).first()
        if not package:
            raise PinValidationError("No active package configured for PIN purchase.")

        price_per_pin = package.price
        total_amount = float(quantity * price_per_pin)
        bv_per_pin = package.bv

        now_ts = int(datetime.utcnow().timestamp())
        order_code = f"SPO-{now_ts % 10000000:07d}-{secrets.token_hex(2).upper()}"

        order = SecurityPinOrder(
            order_code=order_code,
            user_id=user_id,
            package_id=package.id,
            quantity=quantity,
            price_per_pin=price_per_pin,
            total_amount=total_amount,
            bv_per_pin=bv_per_pin,
            payment_method=payment_method or "UPI_TRANSFER",
            payment_reference=payment_reference.strip() if payment_reference else None,
            payment_proof_url=payment_proof_url,
            status='PAYMENT_SUBMITTED' if payment_reference else 'PAYMENT_PENDING',
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()

        log_action(db, 'PIN_ORDER_CREATED', 'SecurityPinOrder', order.id, user_id, {
            'order_code': order.order_code,
            'quantity': quantity,
            'total_amount': total_amount
        })

        return order

    @staticmethod
    def admin_verify_order_payment(
        db: Session,
        order_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None
    ) -> SecurityPinOrder:
        order = db.get(SecurityPinOrder, order_id)
        if not order:
            raise PinValidationError("PIN Order not found.")

        if order.status not in ('PAYMENT_SUBMITTED', 'PAYMENT_PENDING', 'UNDER_REVIEW'):
            raise PinValidationError(f"Cannot verify order in status '{order.status}'.")

        order.status = 'PAYMENT_VERIFIED'
        order.verified_at = datetime.utcnow()
        order.verified_by = admin_id
        if admin_notes:
            order.admin_notes = admin_notes.strip()

        db.flush()

        log_action(db, 'PIN_ORDER_PAYMENT_VERIFIED', 'SecurityPinOrder', order.id, admin_id, {
            'order_code': order.order_code,
            'total_amount': order.total_amount
        })

        return order

    @staticmethod
    def admin_reject_order(
        db: Session,
        order_id: int,
        admin_id: int,
        rejection_reason: str
    ) -> SecurityPinOrder:
        order = db.get(SecurityPinOrder, order_id)
        if not order:
            raise PinValidationError("PIN Order not found.")

        if order.status == 'COMPLETED':
            raise PinValidationError("Cannot reject an already fulfilled PIN order.")

        order.status = 'REJECTED'
        order.rejection_reason = rejection_reason.strip()
        db.flush()

        log_action(db, 'PIN_ORDER_REJECTED', 'SecurityPinOrder', order.id, admin_id, {
            'order_code': order.order_code,
            'reason': rejection_reason
        })

        return order

    @staticmethod
    def admin_issue_pin_batch(
        db: Session,
        order_id: int,
        admin_id: int,
        expires_in_days: int = 30
    ) -> Tuple[SecurityPinOrder, List[Dict[str, Any]]]:
        """
        Generates EXACTLY order.quantity cryptographically unique single-use PINs
        and credits them into buyer's Security PIN inventory.
        """
        order = db.get(SecurityPinOrder, order_id)
        if not order:
            raise PinValidationError("PIN Order not found.")

        if order.status != 'PAYMENT_VERIFIED':
            raise PinValidationError(f"Payment must be VERIFIED before issuing PINs (Current status: {order.status}).")

        now_dt = datetime.utcnow()
        expires_dt = now_dt + timedelta(days=expires_in_days)
        
        created_pins = []
        raw_pins_export = []

        for _ in range(order.quantity):
            pin_code, raw_pin, pin_hash = PinService.generate_secure_pin()
            
            pin = SecurityPin(
                pin_code=pin_code,
                pin_hash=pin_hash,
                user_id=order.user_id,
                owner_user_id=order.user_id,
                original_owner_user_id=order.user_id,
                order_id=order.id,
                package_id=order.package_id,
                amount=order.price_per_pin,
                bv=order.bv_per_pin,
                status='AVAILABLE',
                created_at=now_dt,
                issued_at=now_dt,
                expires_at=expires_dt,
                created_by_admin_id=admin_id,
                payment_reference=order.payment_reference,
                payment_verified_at=order.verified_at
            )
            db.add(pin)
            db.flush()

            # Create immutable ledger record
            ledger = SecurityPinLedger(
                pin_id=pin.id,
                user_id=order.user_id,
                action='PIN_PURCHASED',
                reference_id=order.order_code,
                from_user_id=None,
                to_user_id=order.user_id,
                actor_id=admin_id,
                notes=f"Issued via Order {order.order_code}",
                timestamp=now_dt
            )
            db.add(ledger)

            created_pins.append(pin)
            raw_pins_export.append({
                'id': pin.id,
                'pin_code': pin.pin_code,
                'raw_pin': raw_pin, # Displayed only once upon issuance
                'package_id': pin.package_id,
                'amount': pin.amount,
                'bv': pin.bv,
                'expires_at': pin.expires_at.isoformat()
            })

        order.status = 'COMPLETED'
        order.completed_at = now_dt
        db.flush()

        log_action(db, 'PIN_BATCH_ISSUED', 'SecurityPinOrder', order.id, admin_id, {
            'order_code': order.order_code,
            'quantity': order.quantity,
            'buyer_user_id': order.user_id
        })

        return order, raw_pins_export

    # =========================================================================
    # 2. USER PIN WALLET & INVENTORY
    # =========================================================================

    @staticmethod
    def get_user_pin_inventory(db: Session, user_id: int) -> Dict[str, Any]:
        user = db.get(User, user_id)
        if not user:
            raise PinValidationError("User not found.")

        now_dt = datetime.utcnow()

        # Update any expired available pins
        db.query(SecurityPin).filter(
            SecurityPin.owner_user_id == user_id,
            SecurityPin.status.in_(['AVAILABLE', 'ISSUED']),
            SecurityPin.expires_at < now_dt
        ).update({'status': 'EXPIRED'}, synchronize_session=False)
        db.flush()

        # Available PINs currently owned
        available_pins = db.query(SecurityPin).filter(
            SecurityPin.owner_user_id == user_id,
            SecurityPin.status.in_(['AVAILABLE', 'ISSUED']),
            SecurityPin.expires_at >= now_dt
        ).order_by(SecurityPin.id.desc()).all()

        available_count = len(available_pins)

        # Used PINs (either originally owned or used by this user)
        used_count = db.query(SecurityPin).filter(
            or_(
                SecurityPin.owner_user_id == user_id,
                SecurityPin.original_owner_user_id == user_id
            ),
            SecurityPin.status == 'USED'
        ).count()

        # Transferred away PINs (user was original owner, but current owner is someone else)
        transferred_count = db.query(SecurityPinTransfer).filter(
            SecurityPinTransfer.from_user_id == user_id
        ).count()

        # Received PINs from upline (user is current owner, but original owner was someone else)
        received_count = db.query(SecurityPinTransfer).filter(
            SecurityPinTransfer.to_user_id == user_id
        ).count()

        # Expired PINs
        expired_count = db.query(SecurityPin).filter(
            SecurityPin.owner_user_id == user_id,
            SecurityPin.status == 'EXPIRED'
        ).count()

        # Total purchased via orders
        total_purchased = db.query(SecurityPin).filter(
            SecurityPin.original_owner_user_id == user_id
        ).count()

        # Pending incoming upline requests (from downlines to this user)
        pending_downline_requests = db.query(SecurityPinUplineRequest).filter(
            SecurityPinUplineRequest.upline_user_id == user_id,
            SecurityPinUplineRequest.status == 'PENDING'
        ).count()

        return {
            'wallet': {
                'available': available_count,
                'used': used_count,
                'transferred': transferred_count,
                'received': received_count,
                'expired': expired_count,
                'total_purchased': total_purchased,
                'pending_downline_requests': pending_downline_requests
            },
            'available_pins': [p.to_dict(include_pin_code=True) for p in available_pins],
            'user': {
                'id': user.id,
                'user_code': user.user_code,
                'full_name': user.full_name,
                'is_active': user.is_active
            }
        }

    # =========================================================================
    # 3. USE OWN PIN TO ACTIVATE
    # =========================================================================

    @staticmethod
    def user_use_own_pin_to_activate(
        db: Session,
        user_id: int,
        pin_id: Optional[int] = None,
        raw_pin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activates user's own package using an AVAILABLE PIN in their wallet.
        Triggers existing untouched process_package_purchase pipeline.
        """
        user = db.get(User, user_id)
        if not user:
            raise PinValidationError("User not found.")

        if user.is_active:
            raise PinValidationError("Account is already active with a registered package.")

        now_dt = datetime.utcnow()

        # Find available PIN owned by user
        pin_query = db.query(SecurityPin).filter(
            SecurityPin.owner_user_id == user_id,
            SecurityPin.status.in_(['AVAILABLE', 'ISSUED']),
            SecurityPin.expires_at >= now_dt
        ).with_for_update()

        if pin_id:
            pin_query = pin_query.filter(SecurityPin.id == pin_id)
        elif raw_pin:
            clean_pin = raw_pin.strip().upper()
            target_hash = hashlib.sha256(clean_pin.encode('utf-8')).hexdigest()
            pin_query = pin_query.filter(SecurityPin.pin_hash == target_hash)

        pin = pin_query.first()
        if not pin:
            raise PinValidationError("No available Security PIN found in your inventory to activate.")

        # ATOMIC UPDATE
        pin.status = 'USED'
        pin.used_at = now_dt
        pin.user_id = user_id

        # Immutable ledger
        ledger = SecurityPinLedger(
            pin_id=pin.id,
            user_id=user_id,
            action='PIN_USED',
            reference_id=f"ACTIVATE-{user.user_code}",
            from_user_id=None,
            to_user_id=None,
            actor_id=user_id,
            notes="Package Activated by Owner",
            timestamp=now_dt
        )
        db.add(ledger)

        # Trigger existing MLM purchase pipeline
        idempotency_key = f"PIN-PUR-{pin.id}-{int(now_dt.timestamp())}"
        purchase, events = process_package_purchase(
            db=db,
            user_id=user.id,
            package_id=pin.package_id,
            idempotency_key=idempotency_key
        )

        db.flush()

        log_action(db, 'PACKAGE_ACTIVATED_VIA_PIN_INVENTORY', 'Purchase', purchase.id, user.id, {
            'pin_id': pin.id,
            'pin_code': pin.pin_code,
            'amount': purchase.amount,
            'bv': purchase.bv
        })

        return {
            'purchase': purchase.to_dict(),
            'events': events,
            'pin': pin.to_dict(include_pin_code=False),
            'user': user.to_dict()
        }

    # =========================================================================
    # 4. PIN TRANSFER (GIVE PIN TO DOWNLINE)
    # =========================================================================

    @staticmethod
    def user_transfer_pin_to_downline(
        db: Session,
        from_user_id: int,
        to_user_identifier: Any,
        pin_id: Optional[int] = None,
        quantity: int = 1,
        reason: str = "Downline Package Activation"
    ) -> List[Dict[str, Any]]:
        """
        Atomically transfers ownership of `quantity` available PINs
        from `from_user_id` to eligible downline `to_user_id`.
        """
        from_user = db.get(User, from_user_id)
        if not from_user:
            raise PinValidationError("Sender user not found.")

        # Resolve recipient
        to_user = None
        if isinstance(to_user_identifier, int) or (isinstance(to_user_identifier, str) and to_user_identifier.isdigit()):
            to_user = db.get(User, int(to_user_identifier))
        elif isinstance(to_user_identifier, str):
            identifier = to_user_identifier.strip()
            to_user = db.query(User).filter(
                or_(
                    User.user_code == identifier.upper(),
                    User.email == identifier.lower(),
                    User.mobile == identifier
                )
            ).first()

        if not to_user:
            raise PinValidationError("Recipient user not found. Please verify user code or email.")

        if to_user.id == from_user_id:
            raise PinValidationError("Cannot transfer PIN to yourself.")

        # Check Downline Eligibility
        if not PinService.is_user_in_downline(db, ancestor_id=from_user_id, descendant_id=to_user.id):
            raise PinValidationError(
                f"Transfer rejected: {to_user.full_name} ({to_user.user_code}) is not in your eligible downline network."
            )

        now_dt = datetime.utcnow()

        # Query available PINs owned by sender with row-level lock
        query = db.query(SecurityPin).filter(
            SecurityPin.owner_user_id == from_user_id,
            SecurityPin.status.in_(['AVAILABLE', 'ISSUED']),
            SecurityPin.expires_at >= now_dt
        ).with_for_update()

        if pin_id:
            query = query.filter(SecurityPin.id == pin_id)

        available_pins = query.limit(quantity).all()

        if len(available_pins) < quantity:
            raise PinValidationError(
                f"Insufficient available PINs. You requested {quantity} PIN(s), but only {len(available_pins)} are available."
            )

        transferred_records = []

        for pin in available_pins:
            # Transfer ownership
            pin.owner_user_id = to_user.id
            pin.user_id = to_user.id # Maintain compatibility
            pin.transferred_at = now_dt
            pin.status = 'AVAILABLE' # Available to recipient

            # Transfer audit record
            transfer = SecurityPinTransfer(
                pin_id=pin.id,
                from_user_id=from_user_id,
                to_user_id=to_user.id,
                transfer_reason=reason,
                transferred_at=now_dt,
                created_by_user_id=from_user_id,
                status='COMPLETED'
            )
            db.add(transfer)

            # Sender Ledger
            db.add(SecurityPinLedger(
                pin_id=pin.id,
                user_id=from_user_id,
                action='PIN_TRANSFERRED',
                reference_id=f"TRF-{pin.id}",
                from_user_id=from_user_id,
                to_user_id=to_user.id,
                actor_id=from_user_id,
                notes=reason,
                timestamp=now_dt
            ))

            # Recipient Ledger
            db.add(SecurityPinLedger(
                pin_id=pin.id,
                user_id=to_user.id,
                action='PIN_TRANSFER_RECEIVED',
                reference_id=f"TRF-{pin.id}",
                from_user_id=from_user_id,
                to_user_id=to_user.id,
                actor_id=from_user_id,
                notes=reason,
                timestamp=now_dt
            ))

            transferred_records.append(pin.to_dict(include_pin_code=True))

        db.flush()

        log_action(db, 'PIN_TRANSFERRED', 'User', to_user.id, from_user_id, {
            'count': len(transferred_records),
            'recipient_code': to_user.user_code,
            'reason': reason
        })

        return transferred_records

    # =========================================================================
    # 5. UPLINE PIN REQUESTS (DOWNLINE REQUESTS PIN FROM SPONSOR/UPLINE)
    # =========================================================================

    @staticmethod
    def request_pin_from_upline(
        db: Session,
        requester_user_id: int,
        upline_id: Optional[int] = None,
        package_id: Optional[int] = 1,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> SecurityPinUplineRequest:
        requester = db.get(User, requester_user_id)
        if not requester:
            raise PinValidationError("Requester not found.")

        # Default upline is sponsor, then binary parent
        target_upline_id = upline_id or requester.sponsor_id or requester.binary_parent_id
        if not target_upline_id:
            raise PinValidationError("No sponsor or upline found to request PIN from.")

        upline = db.get(User, target_upline_id)
        if not upline:
            raise PinValidationError("Upline sponsor not found.")

        package = db.get(Package, package_id) or db.query(Package).filter(Package.is_active == True).first()
        if not package:
            raise PinValidationError("Package not configured.")

        now_ts = int(datetime.utcnow().timestamp())
        request_code = f"UPR-{now_ts % 10000000:07d}-{secrets.token_hex(2).upper()}"

        req = SecurityPinUplineRequest(
            request_code=request_code,
            requester_user_id=requester_user_id,
            upline_user_id=target_upline_id,
            package_id=package.id,
            quantity=quantity,
            status='PENDING',
            notes=notes.strip() if notes else None,
            created_at=datetime.utcnow()
        )
        db.add(req)
        db.flush()

        log_action(db, 'PIN_REQUEST_TO_UPLINE', 'SecurityPinUplineRequest', req.id, requester_user_id, {
            'request_code': req.request_code,
            'upline_id': target_upline_id,
            'quantity': quantity
        })

        return req

    @staticmethod
    def upline_approve_pin_request(
        db: Session,
        request_id: int,
        upline_user_id: int
    ) -> Dict[str, Any]:
        """Upline approves request and transfers PIN(s) to requester."""
        req = db.query(SecurityPinUplineRequest).filter(
            SecurityPinUplineRequest.id == request_id
        ).with_for_update().first()

        if not req:
            raise PinValidationError("PIN Request not found.")

        if req.upline_user_id != upline_user_id:
            raise PinSecurityError("Unauthorized: You are not the assigned upline for this request.")

        if req.status != 'PENDING':
            raise PinValidationError(f"Cannot approve request with status '{req.status}'.")

        # Transfer PINs from upline to requester
        transferred = PinService.user_transfer_pin_to_downline(
            db=db,
            from_user_id=upline_user_id,
            to_user_identifier=req.requester_user_id,
            quantity=req.quantity,
            reason=f"Approved Upline Request {req.request_code}"
        )

        req.status = 'APPROVED'
        req.responded_at = datetime.utcnow()
        if transferred:
            req.transferred_pin_id = transferred[0]['id']

        db.flush()

        log_action(db, 'UPLINE_PIN_REQUEST_APPROVED', 'SecurityPinUplineRequest', req.id, upline_user_id, {
            'request_code': req.request_code,
            'requester_id': req.requester_user_id,
            'quantity': req.quantity
        })

        return {
            'request': req.to_dict(),
            'transferred_pins': transferred
        }

    @staticmethod
    def upline_reject_pin_request(
        db: Session,
        request_id: int,
        upline_user_id: int,
        reason: str = "Request declined"
    ) -> SecurityPinUplineRequest:
        req = db.get(SecurityPinUplineRequest, request_id)
        if not req:
            raise PinValidationError("PIN Request not found.")

        if req.upline_user_id != upline_user_id:
            raise PinSecurityError("Unauthorized: You are not the assigned upline for this request.")

        if req.status != 'PENDING':
            raise PinValidationError(f"Cannot reject request with status '{req.status}'.")

        req.status = 'REJECTED'
        req.rejection_reason = reason.strip()
        req.responded_at = datetime.utcnow()
        db.flush()

        log_action(db, 'UPLINE_PIN_REQUEST_REJECTED', 'SecurityPinUplineRequest', req.id, upline_user_id, {
            'request_code': req.request_code,
            'reason': reason
        })

        return req

    # =========================================================================
    # 6. LEGACY ACTIVATION REQUEST COMPATIBILITY (SINGLE PIN ACTIVATION)
    # =========================================================================

    @staticmethod
    # =========================================================================
    # 6. LEGACY ACTIVATION REQUEST COMPATIBILITY (SINGLE PIN ACTIVATION)
    # =========================================================================

    @staticmethod
    def get_or_create_activation_request(
        db: Session,
        user_id: int,
        package_id: Optional[int] = None,
        payment_method: str = "UPI_TRANSFER",
        payment_reference: Optional[str] = None,
        payment_proof_url: Optional[str] = None,
        admin_notes: Optional[str] = None
    ) -> PackageActivationRequest:
        user = db.get(User, user_id)
        if not user:
            raise PinSecurityError("User account not found.")

        if user.is_active:
            raise PinSecurityError("User already has an active package.")

        package = db.get(Package, package_id) if package_id else db.query(Package).filter(Package.is_active == True).first()
        if not package:
            raise PinSecurityError("No active package found.")

        existing_req = db.query(PackageActivationRequest).filter(
            PackageActivationRequest.user_id == user_id,
            PackageActivationRequest.status.in_([
                'PAYMENT_PENDING', 'PAYMENT_SUBMITTED', 'UNDER_REVIEW', 'PAYMENT_VERIFIED', 'PIN_ISSUED'
            ])
        ).order_by(PackageActivationRequest.id.desc()).first()

        if existing_req:
            if payment_reference:
                existing_req.payment_reference = payment_reference.strip()
                existing_req.payment_method = payment_method or existing_req.payment_method
                if payment_proof_url:
                    existing_req.payment_proof_url = payment_proof_url
                if existing_req.status == 'PAYMENT_PENDING':
                    existing_req.status = 'PAYMENT_SUBMITTED'
                db.flush()
            return existing_req

        now_ts = int(datetime.utcnow().timestamp())
        request_code = f"REQ-{now_ts % 10000000:07d}-{secrets.token_hex(2).upper()}"
        recipient_id = user.sponsor_id or user.binary_parent_id

        req = PackageActivationRequest(
            request_code=request_code,
            user_id=user.id,
            package_id=package.id,
            package_amount=package.price,
            package_bv=package.bv,
            payment_method=payment_method or "UPI_TRANSFER",
            payment_reference=payment_reference.strip() if payment_reference else None,
            payment_recipient_id=recipient_id,
            payment_proof_url=payment_proof_url,
            status='PAYMENT_SUBMITTED' if payment_reference else 'PAYMENT_PENDING',
            admin_notes=admin_notes,
            requested_at=datetime.utcnow()
        )
        db.add(req)
        db.flush()
        return req

    @staticmethod
    def submit_payment(
        db: Session,
        user_id: int,
        request_id: Optional[int] = None,
        payment_method: str = "UPI_TRANSFER",
        payment_reference: str = "",
        payment_proof_url: Optional[str] = None
    ) -> PackageActivationRequest:
        if not payment_reference or not payment_reference.strip():
            raise PinSecurityError("Payment reference / UTR number is required.")

        req = None
        if request_id:
            req = db.get(PackageActivationRequest, request_id)
        if not req:
            req = db.query(PackageActivationRequest).filter(
                PackageActivationRequest.user_id == user_id,
                PackageActivationRequest.status.in_(['PAYMENT_PENDING', 'PAYMENT_SUBMITTED', 'UNDER_REVIEW'])
            ).order_by(PackageActivationRequest.id.desc()).first()

        if not req:
            req = PinService.get_or_create_activation_request(
                db=db,
                user_id=user_id,
                payment_method=payment_method,
                payment_reference=payment_reference,
                payment_proof_url=payment_proof_url
            )
            return req

        req.payment_method = payment_method
        req.payment_reference = payment_reference.strip()
        if payment_proof_url:
            req.payment_proof_url = payment_proof_url
        req.status = 'PAYMENT_SUBMITTED'
        db.flush()
        return req

    @staticmethod
    def verify_payment(
        db: Session,
        request_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None
    ) -> PackageActivationRequest:
        req = db.get(PackageActivationRequest, request_id)
        if not req:
            raise PinSecurityError("Activation request not found.")

        if req.status not in ('PAYMENT_SUBMITTED', 'PAYMENT_PENDING', 'UNDER_REVIEW'):
            raise PinSecurityError(f"Cannot verify request in status '{req.status}'.")

        req.status = 'PAYMENT_VERIFIED'
        req.verified_at = datetime.utcnow()
        req.verified_by = admin_id
        if admin_notes:
            req.admin_notes = admin_notes.strip()

        db.flush()
        return req

    @staticmethod
    def reject_request(
        db: Session,
        request_id: int,
        admin_id: int,
        reason: str
    ) -> PackageActivationRequest:
        req = db.get(PackageActivationRequest, request_id)
        if not req:
            raise PinSecurityError("Activation request not found.")

        if req.status == 'ACTIVATED':
            raise PinSecurityError("Cannot reject an already activated package.")

        req.status = 'REJECTED'
        req.rejection_reason = reason
        db.flush()
        return req

    @staticmethod
    def issue_security_pin(
        db: Session,
        request_id: int,
        admin_id: int,
        expires_in_days: int = 7
    ) -> Tuple[SecurityPin, str]:
        req = db.get(PackageActivationRequest, request_id)
        if not req:
            raise PinSecurityError("Activation request not found.")

        if req.status != 'PAYMENT_VERIFIED':
            raise PinSecurityError(f"Payment must be verified first before issuing a PIN (Current status: {req.status}).")

        pin_code, raw_pin, pin_hash = PinService.generate_secure_pin()
        now_dt = datetime.utcnow()
        expires_dt = now_dt + timedelta(days=expires_in_days)

        pin = SecurityPin(
            pin_code=pin_code,
            pin_hash=pin_hash,
            user_id=req.user_id,
            owner_user_id=req.user_id,
            original_owner_user_id=req.user_id,
            package_id=req.package_id,
            activation_request_id=req.id,
            amount=req.package_amount,
            bv=req.package_bv,
            status='AVAILABLE',
            created_at=now_dt,
            issued_at=now_dt,
            expires_at=expires_dt,
            created_by_admin_id=admin_id,
            payment_reference=req.payment_reference,
            payment_verified_at=req.verified_at
        )
        db.add(pin)
        db.flush()

        req.status = 'PIN_ISSUED'
        req.security_pin_id = pin.id
        db.flush()

        return pin, raw_pin

    @staticmethod
    def activate_package_with_pin(
        db: Session,
        user_id: int,
        raw_pin: str,
        request_id: Optional[int] = None
    ) -> dict:
        """
        Validates PIN with strict security checks, locks the row atomically,
        marks PIN as USED, and calls existing process_package_purchase pipeline.
        """
        user = db.get(User, user_id)
        if not user:
            raise PinValidationError("User account not found.")

        if user.is_active:
            raise PinValidationError("Account is already active with a registered package.")

        if not raw_pin or not raw_pin.strip():
            raise PinValidationError("Security PIN is required.")

        clean_pin = raw_pin.strip().upper()
        target_hash = hashlib.sha256(clean_pin.encode('utf-8')).hexdigest()

        # Row-level lock query for atomicity and double-activation prevention
        pin_query = db.query(SecurityPin).filter(
            or_(
                SecurityPin.owner_user_id == user_id,
                SecurityPin.user_id == user_id
            ),
            SecurityPin.pin_hash == target_hash
        ).with_for_update()

        pin = pin_query.first()

        # If PIN doesn't match this user or hash
        if not pin:
            # Increment attempt counter on any pending PIN for this user
            active_pin = db.query(SecurityPin).filter(
                or_(
                    SecurityPin.owner_user_id == user_id,
                    SecurityPin.user_id == user_id
                ),
                SecurityPin.status.in_(['AVAILABLE', 'ISSUED'])
            ).first()

            if active_pin:
                active_pin.attempt_count += 1
                if active_pin.attempt_count >= active_pin.max_attempts:
                    active_pin.status = 'REVOKED'
                    active_pin.revocation_reason = "Maximum PIN attempts exceeded."

            log_action(db, 'PIN_ATTEMPT_FAILED', 'User', user_id, user_id, {
                'reason': 'Invalid PIN hash'
            })
            db.commit()
            raise PinValidationError("Invalid or unavailable Security PIN.")

        # Check PIN Status
        if pin.status == 'USED':
            raise PinValidationError("Security PIN has already been used.")

        if pin.status == 'REVOKED':
            raise PinValidationError("Security PIN has been revoked or locked.")

        if pin.status == 'EXPIRED' or pin.expires_at < datetime.utcnow():
            pin.status = 'EXPIRED'
            db.flush()
            raise PinValidationError("Security PIN has expired. Please contact admin for a new PIN.")

        if pin.status not in ('AVAILABLE', 'ISSUED'):
            raise PinValidationError(f"Security PIN is not valid for activation (Status: {pin.status}).")

        # Resolve activation request
        req = None
        if request_id:
            req = db.get(PackageActivationRequest, request_id)
        if not req and pin.activation_request_id:
            req = db.get(PackageActivationRequest, pin.activation_request_id)
        if not req:
            req = db.query(PackageActivationRequest).filter(
                PackageActivationRequest.user_id == user_id,
                PackageActivationRequest.status.in_(['PIN_ISSUED', 'PAYMENT_VERIFIED'])
            ).order_by(PackageActivationRequest.id.desc()).first()

        # ATOMIC EXECUTION:
        now_dt = datetime.utcnow()
        pin.status = 'USED'
        pin.used_at = now_dt

        if req:
            req.status = 'ACTIVATED'
            req.activated_at = now_dt

        # Immutable ledger
        db.add(SecurityPinLedger(
            pin_id=pin.id,
            user_id=user_id,
            action='PIN_USED',
            reference_id=f"ACTIVATE-{user.user_code}",
            actor_id=user_id,
            notes="Package Activated by User",
            timestamp=now_dt
        ))

        # Trigger existing MLM purchase pipeline
        idempotency_key = f"PIN-PUR-{pin.id}-{int(now_dt.timestamp())}"
        purchase, events = process_package_purchase(
            db=db,
            user_id=user.id,
            package_id=pin.package_id,
            idempotency_key=idempotency_key
        )

        if req:
            req.purchase_id = purchase.id

        db.flush()

        log_action(db, 'PACKAGE_ACTIVATED', 'Purchase', purchase.id, user.id, {
            'pin_id': pin.id,
            'pin_code': pin.pin_code,
            'amount': purchase.amount,
            'bv': purchase.bv
        })

        return {
            'purchase': purchase.to_dict(),
            'events': events,
            'pin': pin.to_dict(include_pin_code=False),
            'activation_request': req.to_dict() if req else None,
            'user': user.to_dict()
        }

    @staticmethod
    def revoke_security_pin(
        db: Session,
        pin_id: int,
        admin_id: int,
        reason: str
    ) -> SecurityPin:
        pin = db.get(SecurityPin, pin_id)
        if not pin:
            raise PinSecurityError("Security PIN not found.")

        if pin.status == 'USED':
            raise PinSecurityError("Cannot revoke a PIN that has already been used.")

        pin.status = 'REVOKED'
        pin.revocation_reason = reason
        db.flush()

        # Immutable ledger
        db.add(SecurityPinLedger(
            pin_id=pin.id,
            user_id=pin.owner_user_id,
            action='PIN_REVOKED',
            actor_id=admin_id,
            notes=reason,
            timestamp=datetime.utcnow()
        ))

        return pin

    @staticmethod
    def revoke_pin(db: Session, pin_id: int, admin_id: int, reason: str) -> SecurityPin:
        return PinService.revoke_security_pin(db, pin_id, admin_id, reason)

pin_service = PinService()
