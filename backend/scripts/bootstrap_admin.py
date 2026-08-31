"""
Production Administrator Bootstrap Utility
==========================================
Explicit, idempotent, one-time administrator provisioning utility for AWS RDS PostgreSQL
and local environments.

Usage:
  python backend/scripts/bootstrap_admin.py --email admin@domain.com --password "SecurePass123!"
  or
  export INITIAL_ADMIN_EMAIL="admin@domain.com"
  export INITIAL_ADMIN_PASSWORD="SecurePass123!"
  python backend/scripts/bootstrap_admin.py
"""

import os
import sys
import argparse
import datetime

# Reconfigure stdout for UTF-8 on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, SessionLocal, Base, apply_migrations
from app.models.user import User
from app.security import hash_password, verify_password
from app.services.wallet_service import get_or_create_wallet
from app.services.mlm_service import get_or_create_binary_volume
from app.services.audit_service import log_action

def bootstrap_admin(
    email: str,
    password: str,
    full_name: str = "System Admin",
    mobile: str = "9876500001",
    force_reset: bool = False
) -> bool:
    email = (email or "").strip().lower()
    password = (password or "").strip()

    if not email or "@" not in email or "." not in email:
        print("[ERROR] A valid administrator email address is required.")
        return False

    if not password or len(password) < 8:
        print("[ERROR] Administrator password must be at least 8 characters long.")
        return False

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)

    db: Session = SessionLocal()
    try:
        existing_admin = db.query(User).filter((User.role == "ADMIN") | (User.email == email)).first()

        if existing_admin:
            if force_reset:
                existing_admin.password_hash = hash_password(password)
                existing_admin.is_active = True
                log_action(db, 'ADMIN_PASSWORD_RESET_CLI', 'User', existing_admin.id, existing_admin.id, {
                    'email': existing_admin.email,
                    'action': 'Password reset via administrative CLI'
                })
                db.commit()
                print(f"[SUCCESS] Password for administrator '{existing_admin.email}' updated successfully.")
                return True
            else:
                print(f"[INFO] Administrator account '{existing_admin.email}' (ID: {existing_admin.id}, Code: {existing_admin.user_code}) already exists.")
                print("[INFO] Existing password was NOT modified. To reset password, provide --force-reset or use /api/auth/change-password.")
                return True

        # Create new admin
        admin = User(
            user_code="USR-00001",
            email=email,
            mobile=mobile.strip(),
            full_name=full_name.strip(),
            password_hash=hash_password(password),
            role="ADMIN",
            referral_code="ADMIN001",
            is_active=True
        )
        db.add(admin)
        db.flush()

        get_or_create_wallet(db, admin.id)
        get_or_create_binary_volume(db, admin.id)

        log_action(db, 'ADMIN_BOOTSTRAPPED_CLI', 'User', admin.id, admin.id, {
            'email': email,
            'status': 'Administrator provisioned via administrative CLI'
        })
        db.commit()

        print(f"[SUCCESS] Initial administrator account '{email}' (Code: {admin.user_code}) created successfully!")
        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to bootstrap administrator: {e}")
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Bootstrap or manage administrator account")
    parser.add_argument("--email", default=os.getenv("INITIAL_ADMIN_EMAIL"), help="Admin email address")
    parser.add_argument("--password", default=os.getenv("INITIAL_ADMIN_PASSWORD"), help="Admin password (min 8 chars)")
    parser.add_argument("--name", default=os.getenv("INITIAL_ADMIN_NAME", "System Admin"), help="Admin full name")
    parser.add_argument("--mobile", default=os.getenv("INITIAL_ADMIN_MOBILE", "9876500001"), help="Admin mobile number")
    parser.add_argument("--force-reset", action="store_true", help="Force update password if admin already exists")

    args = parser.parse_args()

    email = args.email
    password = args.password

    if not email:
        email = input("Enter Administrator Email: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Enter Administrator Password (min 8 chars): ").strip()

    success = bootstrap_admin(
        email=email,
        password=password,
        full_name=args.name,
        mobile=args.mobile,
        force_reset=args.force_reset
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
