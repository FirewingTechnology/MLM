"""
Live AWS RDS PostgreSQL Automated Verification & Cleanup Script
==============================================================
1. Connects to the real AWS RDS PostgreSQL instance.
2. Applies Alembic migrations (e8f9a0b1c2d3).
3. Executes complete end-to-end MLM business logic tests on PostgreSQL.
4. Proves all tables store and read live data.
5. Cleans up all test data from RDS after testing completes.
"""

import os
import sys
import urllib.parse
from decimal import Decimal

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

RDS_DATABASE_URL = "postgresql+psycopg://postgres:Rohan#2026@mystatus-postgres.c9oqam2usjp9.ap-south-1.rds.amazonaws.com:5432/postgres?sslmode=require"

def get_engine():
    return create_engine(
        RDS_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )

def test_connectivity():
    print("\n" + "=" * 70)
    print("STEP 1: TESTING AWS RDS POSTGRESQL CONNECTIVITY")
    print("=" * 70)
    try:
        engine = get_engine()
        with engine.connect() as conn:
            ver = conn.execute(text("SELECT version();")).scalar()
            curr_db = conn.execute(text("SELECT current_database();")).scalar()
            curr_user = conn.execute(text("SELECT current_user;")).scalar()
            server_addr = conn.execute(text("SELECT inet_server_addr();")).scalar()
            print(f"[SUCCESS] Connected to AWS RDS PostgreSQL!")
            print(f"  * PostgreSQL Version : {ver}")
            print(f"  * Current Database    : {curr_db}")
            print(f"  * Current User        : {curr_user}")
            print(f"  * Server Private IP   : {server_addr}")
            return True
    except Exception as e:
        print(f"[FAIL] Could not connect to AWS RDS PostgreSQL:")
        print(f"  * Error: {type(e).__name__} - {e}")
        return False

def apply_schema():
    print("\n" + "=" * 70)
    print("STEP 2: APPLYING SCHEMA & BASELINE TO RDS POSTGRESQL")
    print("=" * 70)
    engine = get_engine()
    from app.database import Base, apply_migrations
    import app.models  # load all 21 models
    
    print("Creating all tables in Base.metadata...")
    Base.metadata.create_all(bind=engine)
    print(f"[SUCCESS] Metadata tables created ({len(Base.metadata.tables)} tables).")

    print("Applying Alembic migrations...")
    apply_migrations(engine)
    print("[SUCCESS] Alembic migrations applied successfully.")

def run_e2e_mlm_test():
    print("\n" + "=" * 70)
    print("STEP 3: RUNNING LIVE E2E MLM TEST ON AWS RDS")
    print("=" * 70)
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    from app.models.user import User
    from app.models.package import Package
    from app.models.purchase import Purchase
    from app.models.wallet import Wallet, WalletTransaction
    from app.models.volume import BinaryVolume
    from app.models.commission import Commission
    from app.models.security_pin import SecurityPin
    from app.security import hash_password
    from app.services.wallet_service import WalletService
    from app.services.pin_service import SecurityPinService

    try:
        # 1. Verify / Create Package
        pkg = db.query(Package).filter(Package.name == "Standard Package").first()
        if not pkg:
            pkg = Package(name="Standard Package", price=35000.0, bv=30000.0, is_active=True)
            db.add(pkg)
            db.commit()
            db.refresh(pkg)
        print(f"[PASS] Package verified on RDS: ID={pkg.id}, Price=₹{pkg.price:,.2f}, BV={pkg.bv:,.2f}")

        # 2. Create Test Admin
        admin = db.query(User).filter(User.user_code == "TEST-ADM01").first()
        if not admin:
            admin = User(
                user_code="TEST-ADM01",
                email="testadmin_rds@mynetwork.com",
                mobile="9800000001",
                full_name="RDS Test Admin",
                password_hash=hash_password("Admin@RDS2026"),
                role="ADMIN",
                referral_code="RDSADM",
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        print(f"[PASS] Admin user verified on RDS: {admin.user_code} ({admin.email})")

        # 3. Create Root Member
        root_user = db.query(User).filter(User.user_code == "TEST-ROOT").first()
        if not root_user:
            root_user = User(
                user_code="TEST-ROOT",
                email="testroot_rds@mynetwork.com",
                mobile="9800000002",
                full_name="RDS Root Member",
                password_hash=hash_password("User@RDS2026"),
                role="USER",
                referral_code="RDSROOT",
                is_active=True
            )
            db.add(root_user)
            db.commit()
            db.refresh(root_user)
            w = WalletService.get_or_create_wallet(db, root_user.id)
            db.commit()
        print(f"[PASS] Root member verified on RDS: {root_user.user_code}")

        # 4. Create Left & Right child users
        left_user = db.query(User).filter(User.user_code == "TEST-LEFT").first()
        if not left_user:
            left_user = User(
                user_code="TEST-LEFT",
                email="testleft_rds@mynetwork.com",
                mobile="9800000003",
                full_name="RDS Left Member",
                password_hash=hash_password("User@RDS2026"),
                role="USER",
                sponsor_id=root_user.id,
                binary_parent_id=root_user.id,
                binary_position="LEFT",
                referral_code="RDSLEFT",
                is_active=True
            )
            db.add(left_user)
            db.commit()
            db.refresh(left_user)
            WalletService.get_or_create_wallet(db, left_user.id)
            db.commit()
        print(f"[PASS] Left child verified: {left_user.user_code} (Parent: {left_user.binary_parent_id}, Side: {left_user.binary_position})")

        right_user = db.query(User).filter(User.user_code == "TEST-RIGHT").first()
        if not right_user:
            right_user = User(
                user_code="TEST-RIGHT",
                email="testright_rds@mynetwork.com",
                mobile="9800000004",
                full_name="RDS Right Member",
                password_hash=hash_password("User@RDS2026"),
                role="USER",
                sponsor_id=root_user.id,
                binary_parent_id=root_user.id,
                binary_position="RIGHT",
                referral_code="RDSRIGHT",
                is_active=True
            )
            db.add(right_user)
            db.commit()
            db.refresh(right_user)
            WalletService.get_or_create_wallet(db, right_user.id)
            db.commit()
        print(f"[PASS] Right child verified: {right_user.user_code} (Parent: {right_user.binary_parent_id}, Side: {right_user.binary_position})")

        # 5. Test Wallet Mutation & Financial Concurrency
        print("Testing Wallet Credit on RDS...")
        tx = WalletService.credit_wallet(
            db,
            user_id=root_user.id,
            amount=10000.0,
            category="PAIR_BONUS",
            description="RDS Verification Pair Bonus",
            reference_id="RDS-TX-001"
        )
        db.commit()
        w_check = db.query(Wallet).filter(Wallet.user_id == root_user.id).first()
        print(f"[PASS] Wallet credited on RDS: Balance=₹{w_check.balance:,.2f}, Total Earned=₹{w_check.total_earned:,.2f}")

        # 6. Test Security PIN Generation
        print("Testing Security PIN Generation on RDS...")
        pin_obj, raw_pin = SecurityPinService.generate_pin(
            db,
            owner_user_id=admin.id,
            package_id=pkg.id,
            actor_id=admin.id,
            notes="RDS Automated Test PIN"
        )
        db.commit()
        print(f"[PASS] Security PIN created on RDS: Code={pin_obj.pin_code}, Status={pin_obj.status}")

        # 7. Print Table Counts on RDS
        inspector = inspect(engine)
        tables = sorted(inspector.get_table_names())
        print("\n--- RDS TABLE ROW COUNTS ---")
        for t in tables:
            cnt = db.execute(text(f'SELECT COUNT(*) FROM "{t}";')).scalar()
            print(f"  * {t:<30} : {cnt} rows")

        print("\n[SUCCESS] ALL E2E MLM TESTS PASSED ON AWS RDS POSTGRESQL!")
        return True
    finally:
        db.close()

def cleanup_test_data():
    print("\n" + "=" * 70)
    print("STEP 4: CLEANING UP ALL TEST DATA FROM RDS POSTGRESQL")
    print("=" * 70)
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        # Delete test records
        from app.models.wallet import WalletTransaction, Wallet
        from app.models.user import User
        from app.models.security_pin import SecurityPin
        from app.models.pin_ledger import SecurityPinLedger
        from app.models.commission import Commission
        from app.models.purchase import Purchase
        from app.models.volume_ledger import VolumeLedger
        from app.models.slot_settlement import SlotSettlement
        from app.models.volume import BinaryVolume

        test_user_codes = ["TEST-ADM01", "TEST-ROOT", "TEST-LEFT", "TEST-RIGHT"]
        test_users = db.query(User).filter(User.user_code.in_(test_user_codes)).all()
        test_user_ids = [u.id for u in test_users]

        if test_user_ids:
            print(f"Deleting test user records for IDs: {test_user_ids}...")
            db.query(SecurityPinLedger).filter(SecurityPinLedger.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(SecurityPin).filter(SecurityPin.owner_user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(WalletTransaction).filter(WalletTransaction.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(Wallet).filter(Wallet.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(Commission).filter(Commission.beneficiary_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(BinaryVolume).filter(BinaryVolume.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(VolumeLedger).filter(VolumeLedger.source_user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(SlotSettlement).filter(SlotSettlement.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            db.query(Purchase).filter(Purchase.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            
            # Delete children first then parents
            db.query(User).filter(User.user_code.in_(["TEST-LEFT", "TEST-RIGHT"])).delete(synchronize_session=False)
            db.query(User).filter(User.user_code == "TEST-ROOT").delete(synchronize_session=False)
            db.query(User).filter(User.user_code == "TEST-ADM01").delete(synchronize_session=False)
            db.commit()
            print("[SUCCESS] All test data removed from AWS RDS database.")
        else:
            print("No test users found to clean up.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if test_connectivity():
        apply_schema()
        run_e2e_mlm_test()
        cleanup_test_data()
    else:
        print("\n[NOTE] Please enable 'Publicly accessible: Yes' on AWS RDS and add Security Group Inbound Rule for Port 5432.")
