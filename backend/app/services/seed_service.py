from sqlalchemy.orm import Session
from app.security import hash_password
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.models.audit_log import AuditLog
from app.services.mlm_service import get_or_create_binary_volume
from app.services.wallet_service import get_or_create_wallet
from app.services.commission_service import process_package_purchase
from app.services.audit_service import log_action

def seed_database(db: Session):
    """Seeds demo network with Package, Admin, and initial tree (Amol -> Rahul, Priya -> Akash, Neha, Rohit, Sneha)."""
    # 1. Package
    package = db.query(Package).filter(Package.name == "Premium Business Package").first()
    if not package:
        package = Package(
            name="Premium Business Package",
            description="Virtual Business Ownership Package with 30,000 BV and active distributor rights.",
            price=35000.0,
            product_value=30000.0,
            gst_amount=5000.0,
            bv=30000.0,
            is_active=True
        )
        db.add(package)
        db.flush()

    # If users already exist in database, skip re-seeding to prevent constraint conflicts
    if db.query(User).count() > 0:
        db.commit()
        return

    # 2. Admin User
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

    # 3. Root User: Amol
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

    # 4. Rahul (Sponsor: Amol, Placement: Amol LEFT)
    rahul = User(
        user_code="USR-00003",
        email="rahul@demo.com",
        mobile="9876500003",
        full_name="Rahul Verma",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="RAHUL001",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(rahul)
    db.flush()
    get_or_create_wallet(db, rahul.id)
    get_or_create_binary_volume(db, rahul.id)

    # 5. Priya (Sponsor: Amol, Placement: Amol RIGHT)
    priya = User(
        user_code="USR-00004",
        email="priya@demo.com",
        mobile="9876500004",
        full_name="Priya Patel",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="PRIYA001",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(priya)
    db.flush()
    get_or_create_wallet(db, priya.id)
    get_or_create_binary_volume(db, priya.id)

    # 6. Akash (Sponsor: Amol, Placement: Rahul LEFT)
    akash = User(
        user_code="USR-00005",
        email="akash@demo.com",
        mobile="9876500005",
        full_name="Akash Singh",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="AKASH001",
        sponsor_id=amol.id,
        binary_parent_id=rahul.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(akash)
    db.flush()
    get_or_create_wallet(db, akash.id)
    get_or_create_binary_volume(db, akash.id)

    # 7. Neha (Sponsor: Rahul, Placement: Rahul RIGHT)
    neha = User(
        user_code="USR-00006",
        email="neha@demo.com",
        mobile="9876500006",
        full_name="Neha Joshi",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="NEHA001",
        sponsor_id=rahul.id,
        binary_parent_id=rahul.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(neha)
    db.flush()
    get_or_create_wallet(db, neha.id)
    get_or_create_binary_volume(db, neha.id)

    # 8. Rohit (Sponsor: Priya, Placement: Priya LEFT)
    rohit = User(
        user_code="USR-00007",
        email="rohit@demo.com",
        mobile="9876500007",
        full_name="Rohit Gupta",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="ROHIT001",
        sponsor_id=priya.id,
        binary_parent_id=priya.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(rohit)
    db.flush()
    get_or_create_wallet(db, rohit.id)
    get_or_create_binary_volume(db, rohit.id)

    # 9. Sneha (Sponsor: Priya, Placement: Priya RIGHT)
    sneha = User(
        user_code="USR-00008",
        email="sneha@demo.com",
        mobile="9876500008",
        full_name="Sneha Kulkarni",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="SNEHA001",
        sponsor_id=priya.id,
        binary_parent_id=priya.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(sneha)
    db.flush()
    get_or_create_wallet(db, sneha.id)
    get_or_create_binary_volume(db, sneha.id)

    db.commit()

    # 10. Execute simulated purchases so demo shows meaningful BV and commissions
    for member in [amol, rahul, priya, akash, neha, rohit, sneha]:
        process_package_purchase(db, user_id=member.id, package_id=package.id, idempotency_key=f"SEED-PUR-{member.id}")

    log_action(db, 'DATABASE_SEEDED', 'System', None, admin.id, {'status': 'Seed completed successfully'})
    db.commit()

def reset_demo_database(db: Session):
    """Wipes all transactions, commissions, withdrawals, volumes, dummy users, and resets to seed state."""
    db.query(AuditLog).delete()
    db.query(WalletTransaction).delete()
    db.query(Withdrawal).delete()
    db.query(Commission).delete()
    db.query(Purchase).delete()
    db.query(BinaryVolume).delete()
    db.query(Wallet).delete()
    db.query(User).delete()
    db.query(Package).delete()
    db.commit()

    seed_database(db)
    admin = db.query(User).filter(User.email == "admin@demo.com").first()
    log_action(db, 'DEMO_RESET', 'System', None, admin.id if admin else None, {'action': 'Full demo reset executed'})
    db.commit()
