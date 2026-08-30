from sqlalchemy.orm import Session
from app.config import settings
from app.security import hash_password
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.period_volume import BinaryPeriodVolume
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.models.audit_log import AuditLog
from app.models.demo_time import DemoTimeConfig
from app.models.pair_event import PairEvent
from app.services.mlm_service import get_or_create_binary_volume
from app.services.wallet_service import get_or_create_wallet
from app.services.audit_service import log_action
from app.services.time_service import slot_service

def backfill_legacy_slots(db: Session):
    """Backfills slot_id for any existing records where slot_id is null."""
    purchases = db.query(Purchase).filter(Purchase.slot_id.is_(None)).all()
    for p in purchases:
        if p.created_at:
            p.slot_id = slot_service.get_slot_id(p.created_at)

    commissions = db.query(Commission).filter(Commission.slot_id.is_(None)).all()
    for c in commissions:
        if c.created_at:
            c.slot_id = slot_service.get_slot_id(c.created_at)

    txns = db.query(WalletTransaction).filter(WalletTransaction.slot_id.is_(None)).all()
    for t in txns:
        if t.created_at:
            t.slot_id = slot_service.get_slot_id(t.created_at)
    db.flush()

def initialize_production_baseline(db: Session):
    """Safely bootstraps required persistent baseline configuration (Package, Time Config, Initial Admin if empty).
    NEVER deletes, overwrites, or modifies existing database records."""
    # 1. Time Configuration (Default: REAL TIME)
    time_cfg = db.query(DemoTimeConfig).filter(DemoTimeConfig.id == 1).first()
    if not time_cfg:
        time_cfg = DemoTimeConfig(id=1, mode='REAL', virtual_datetime=None)
        db.add(time_cfg)
        db.flush()

    # 2. Default Package (Required for MLM operation)
    package = db.query(Package).first()
    if not package:
        package = Package(
            name="Premium Sub Franchise Package",
            description="Sub Franchise Business Ownership Package with 30,000 BV and active distributor rights.",
            price=35000.0,
            product_value=30000.0,
            gst_amount=5000.0,
            bv=30000.0,
            is_active=True
        )
        db.add(package)
        db.flush()

    # 3. If any users exist in the database, preserve everything and return immediately
    if db.query(User).count() > 0:
        db.commit()
        return

    # 4. First-time deployment bootstrap: Create initial Admin if empty so system is accessible
    admin = User(
        user_code="USR-00001",
        email="admin@platform.com",
        mobile="9876500001",
        full_name="System Admin",
        password_hash=hash_password("Admin@123"),
        role="ADMIN",
        referral_code="ADMIN001",
        is_active=True
    )
    db.add(admin)
    db.flush()
    get_or_create_wallet(db, admin.id)
    get_or_create_binary_volume(db, admin.id)

    log_action(db, 'DATABASE_INITIALIZED', 'System', None, admin.id, {'status': 'Production baseline initialized with initial admin'})
    db.commit()

# Alias for backward compatibility
seed_database = initialize_production_baseline

from app.models.referral_token import ReferralToken
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_upline_request import SecurityPinUplineRequest
from app.models.pin_ledger import SecurityPinLedger
from app.models.activation_request import PackageActivationRequest

def reset_demo_database(db: Session, force: bool = False, confirm_text: str = ""):
    """Explicit ADMIN ONLY reset function.
    Strictly blocked in production unless explicit confirm_text is supplied."""
    if settings.is_production and not force and confirm_text != "CONFIRM_PERMANENT_WIPE":
        raise PermissionError("Database wipe is strictly prohibited in PRODUCTION environment. To override, confirm_text='CONFIRM_PERMANENT_WIPE' is required.")

    db.query(SecurityPinLedger).delete()
    db.query(SecurityPinTransfer).delete()
    db.query(SecurityPinUplineRequest).delete()
    db.query(SecurityPin).delete()
    db.query(SecurityPinOrder).delete()
    db.query(PackageActivationRequest).delete()
    db.query(AuditLog).delete()
    db.query(WalletTransaction).delete()
    db.query(Withdrawal).delete()
    db.query(Commission).delete()
    db.query(PairEvent).delete()
    db.query(SlotSettlement).delete()
    db.query(VolumeLedger).delete()
    db.query(Purchase).delete()
    db.query(BinaryPeriodVolume).delete()
    db.query(BinaryVolume).delete()
    db.query(ReferralToken).delete()
    db.query(Wallet).delete()
    db.query(User).delete()
    db.query(Package).delete()
    db.query(DemoTimeConfig).delete()
    db.commit()

    initialize_production_baseline(db)
    admin = db.query(User).filter(User.role == 'ADMIN').first()
    log_action(db, 'ADMIN_MANUAL_RESET', 'Admin', None, admin.id if admin else None, {'action': 'Explicit manual reset executed'})
    db.commit()

