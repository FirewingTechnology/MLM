from sqlalchemy.orm import Session
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

def seed_database(db: Session):
    """Seeds clean baseline system with Package, Admin, and Root User (Amol) with active Wallets and REAL demo time config."""
    # 1. Demo Time Configuration (Default: REAL TIME)
    time_cfg = db.query(DemoTimeConfig).filter(DemoTimeConfig.id == 1).first()
    if not time_cfg:
        time_cfg = DemoTimeConfig(id=1, mode='REAL', virtual_datetime=None)
        db.add(time_cfg)
        db.flush()

    # 2. Package
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

    # Backfill any legacy records if present
    backfill_legacy_slots(db)

    # If users already exist in database, skip re-seeding to prevent constraint conflicts
    if db.query(User).count() > 0:
        db.commit()
        return

    # 3. Admin User
    admin = User(
        user_code="USR-00001",
        email="admin@demo.com",
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

    # 4. Root User: Amol
    amol = User(
        user_code="USR-00002",
        email="amol@demo.com",
        mobile="9876500002",
        full_name="Amol Sharma",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="AMOL001",
        sponsor_id=None,
        binary_parent_id=None,
        binary_position=None,
        is_active=True
    )
    db.add(amol)
    db.flush()
    get_or_create_wallet(db, amol.id)
    get_or_create_binary_volume(db, amol.id)

    log_action(db, 'DATABASE_SEEDED', 'System', None, admin.id, {'status': 'Clean baseline initialized (Admin & Root User only)'})
    db.commit()

from app.models.referral_token import ReferralToken

def reset_demo_database(db: Session):
    """Wipes all transactions, commissions, withdrawals, volumes, dummy users, and resets to seed state."""
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

    seed_database(db)
    admin = db.query(User).filter(User.email == "admin@demo.com").first()
    log_action(db, 'DEMO_RESET', 'System', None, admin.id if admin else None, {'action': 'Full demo reset executed'})
    db.commit()

