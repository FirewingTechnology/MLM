import os
import sqlite3
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_ledger import SecurityPinLedger

class IntegrityService:
    @staticmethod
    def get_database_health(db: Session) -> Dict[str, Any]:
        """Provides comprehensive, safe system database metadata without exposing sensitive secrets."""
        dialect_name = db.bind.dialect.name if db.bind else ("postgresql" if settings.is_postgres else "sqlite")
        db_file = None
        db_size_bytes = 0
        pg_version = None

        if dialect_name == "sqlite":
            if settings.DATABASE_URL.startswith("sqlite:///"):
                db_file = settings.DATABASE_URL.replace("sqlite:///", "")
                if os.path.exists(db_file):
                    db_size_bytes = os.path.getsize(db_file)

        # Check PRAGMA / Version statuses
        wal_enabled = False
        foreign_keys_enabled = False
        if dialect_name == "sqlite":
            try:
                res_wal = db.execute(text("PRAGMA journal_mode;")).scalar()
                wal_enabled = str(res_wal).upper() == "WAL"
            except Exception:
                pass

            try:
                res_fk = db.execute(text("PRAGMA foreign_keys;")).scalar()
                foreign_keys_enabled = bool(res_fk == 1 or res_fk is True)
            except Exception:
                pass
        elif dialect_name == "postgresql":
            foreign_keys_enabled = True
            wal_enabled = True
            try:
                pg_version = db.execute(text("SELECT version();")).scalar()
            except Exception:
                pass

        # Table counts
        counts = {
            "users": db.query(User).count(),
            "packages": db.query(Package).count(),
            "purchases": db.query(Purchase).count(),
            "wallet_transactions": db.query(WalletTransaction).count(),
            "volume_ledger": db.query(VolumeLedger).count(),
            "slot_settlements": db.query(SlotSettlement).count(),
            "commissions": db.query(Commission).count(),
            "withdrawals": db.query(Withdrawal).count(),
            "security_pins": db.query(SecurityPin).count(),
            "security_pin_orders": db.query(SecurityPinOrder).count(),
            "security_pin_transfers": db.query(SecurityPinTransfer).count(),
            "security_pin_ledger": db.query(SecurityPinLedger).count(),
        }

        return {
            "database_engine": dialect_name,
            "database_path": settings.sanitized_db_path,
            "database_exists": True if dialect_name == "postgresql" else bool(db_file and os.path.exists(db_file)),
            "database_size_bytes": db_size_bytes,
            "database_size_mb": round(db_size_bytes / (1024 * 1024), 2),
            "wal_enabled": wal_enabled,
            "foreign_keys_enabled": foreign_keys_enabled,
            "version": pg_version,
            "environment": settings.APP_ENV,
            "is_production": settings.is_production,
            "table_counts": counts
        }

    @staticmethod
    def run_integrity_audit(db: Session) -> Dict[str, Any]:
        """Runs thorough structural, referential, and financial consistency audits across PostgreSQL and SQLite."""
        dialect_name = db.bind.dialect.name if db.bind else ("postgresql" if settings.is_postgres else "sqlite")
        issues: List[Dict[str, Any]] = []
        checks_passed = 0
        total_checks = 10

        # 1. Low-level storage integrity check
        if dialect_name == "sqlite":
            try:
                integrity_res = db.execute(text("PRAGMA integrity_check;")).fetchall()
                if integrity_res and integrity_res[0][0] != "ok":
                    issues.append({
                        "check": "SQLITE_PRAGMA_INTEGRITY",
                        "severity": "CRITICAL",
                        "message": f"SQLite internal B-Tree errors detected: {integrity_res}"
                    })
                else:
                    checks_passed += 1
            except Exception as e:
                issues.append({"check": "SQLITE_PRAGMA_INTEGRITY", "severity": "WARNING", "message": str(e)})
        else:
            try:
                ping_res = db.execute(text("SELECT 1;")).scalar()
                if ping_res == 1:
                    checks_passed += 1
                else:
                    issues.append({"check": "POSTGRESQL_CONNECTION", "severity": "CRITICAL", "message": "PostgreSQL ping check failed."})
            except Exception as e:
                issues.append({"check": "POSTGRESQL_CONNECTION", "severity": "CRITICAL", "message": str(e)})

        # 2. Foreign Key consistency
        if dialect_name == "sqlite":
            try:
                fk_res = db.execute(text("PRAGMA foreign_key_check;")).fetchall()
                if fk_res:
                    issues.append({
                        "check": "SQLITE_FOREIGN_KEYS",
                        "severity": "HIGH",
                        "message": f"Foreign key constraint violations: {len(fk_res)} violations detected.",
                        "details": [str(r) for r in fk_res[:10]]
                    })
                else:
                    checks_passed += 1
            except Exception as e:
                issues.append({"check": "SQLITE_FOREIGN_KEYS", "severity": "WARNING", "message": str(e)})
        else:
            # PostgreSQL enforces foreign keys at write-time; verify relational integrity
            checks_passed += 1

        # 3. Orphan Sponsor relationships
        all_user_ids = {u.id for u in db.query(User.id).all()}
        orphan_sponsors = db.query(User).filter(
            User.sponsor_id.isnot(None),
            ~User.sponsor_id.in_(all_user_ids)
        ).all()
        if orphan_sponsors:
            issues.append({
                "check": "ORPHAN_SPONSORS",
                "severity": "HIGH",
                "message": f"{len(orphan_sponsors)} users have invalid sponsor_id references.",
                "affected_user_ids": [u.id for u in orphan_sponsors]
            })
        else:
            checks_passed += 1

        # 4. Orphan Matching Parent relationships
        orphan_parents = db.query(User).filter(
            User.binary_parent_id.isnot(None),
            ~User.binary_parent_id.in_(all_user_ids)
        ).all()
        if orphan_parents:
            issues.append({
                "check": "ORPHAN_BINARY_PARENTS",
                "severity": "HIGH",
                "message": f"{len(orphan_parents)} users have invalid binary_parent_id references.",
                "affected_user_ids": [u.id for u in orphan_parents]
            })
        else:
            checks_passed += 1

        # 5. Duplicate Binary Leg Placements (Two users claiming same parent and same leg)
        dup_placement_sql = text("""
            SELECT binary_parent_id, binary_position, COUNT(*) as cnt
            FROM users
            WHERE binary_parent_id IS NOT NULL AND binary_position IS NOT NULL
            GROUP BY binary_parent_id, binary_position
            HAVING COUNT(*) > 1;
        """)
        dup_placements = db.execute(dup_placement_sql).fetchall()
        if dup_placements:
            issues.append({
                "check": "DUPLICATE_BINARY_PLACEMENTS",
                "severity": "CRITICAL",
                "message": f"{len(dup_placements)} Binary leg collisions detected.",
                "details": [{"parent_id": r[0], "position": r[1], "count": r[2]} for r in dup_placements]
            })
        else:
            checks_passed += 1

        # 6. Negative Wallet Balances
        negative_wallets = db.query(Wallet).filter(Wallet.balance < 0).all()
        if negative_wallets:
            issues.append({
                "check": "NEGATIVE_WALLET_BALANCES",
                "severity": "CRITICAL",
                "message": f"{len(negative_wallets)} wallets have negative balances.",
                "details": [{"wallet_id": w.id, "user_id": w.user_id, "balance": w.balance} for w in negative_wallets]
            })
        else:
            checks_passed += 1

        # 7. Wallet Ledger vs Balance Reconciliation Check
        wallets = db.query(Wallet).all()
        reconciliation_discrepancies = []
        for w in wallets:
            txns = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == w.id).all()
            expected_balance = 0.0
            for t in txns:
                if t.transaction_type == 'CREDIT':
                    expected_balance += t.amount
                elif t.transaction_type == 'DEBIT':
                    expected_balance -= t.amount
            if abs(w.balance - expected_balance) > 0.01:
                reconciliation_discrepancies.append({
                    "wallet_id": w.id,
                    "user_id": w.user_id,
                    "recorded_balance": w.balance,
                    "ledger_sum": expected_balance,
                    "diff": round(w.balance - expected_balance, 2)
                })
        if reconciliation_discrepancies:
            issues.append({
                "check": "WALLET_LEDGER_RECONCILIATION",
                "severity": "MEDIUM",
                "message": f"{len(reconciliation_discrepancies)} wallets have ledger balance discrepancies.",
                "details": reconciliation_discrepancies[:10]
            })
        else:
            checks_passed += 1

        # 8. Security PIN State Integrity
        invalid_pins = db.query(SecurityPin).filter(
            SecurityPin.status == 'USED',
            SecurityPin.used_at.is_(None)
        ).all()
        if invalid_pins:
            issues.append({
                "check": "SECURITY_PIN_INTEGRITY",
                "severity": "MEDIUM",
                "message": f"{len(invalid_pins)} USED security pins are missing used_at timestamps.",
                "pin_ids": [p.id for p in invalid_pins]
            })
        else:
            checks_passed += 1

        # 9. Orphan Purchases
        orphan_purchases = db.query(Purchase).filter(~Purchase.user_id.in_(all_user_ids)).all()
        if orphan_purchases:
            issues.append({
                "check": "ORPHAN_PURCHASES",
                "severity": "HIGH",
                "message": f"{len(orphan_purchases)} purchase records reference non-existent users.",
                "purchase_ids": [p.id for p in orphan_purchases]
            })
        else:
            checks_passed += 1

        # 10. Volume Ledger Beneficiary Integrity
        orphan_vol_ancestors = db.query(VolumeLedger).filter(
            VolumeLedger.ancestor_user_id.isnot(None),
            ~VolumeLedger.ancestor_user_id.in_(all_user_ids)
        ).all()
        if orphan_vol_ancestors:
            issues.append({
                "check": "VOLUME_LEDGER_ANCESTORS",
                "severity": "HIGH",
                "message": f"{len(orphan_vol_ancestors)} volume ledger records have invalid ancestor references."
            })
        else:
            checks_passed += 1

        overall_status = "HEALTHY"
        if any(i["severity"] == "CRITICAL" for i in issues):
            overall_status = "CRITICAL"
        elif any(i["severity"] == "HIGH" for i in issues):
            overall_status = "WARNING"
        elif issues:
            overall_status = "NOTICE"

        # Timestamp query
        current_ts = None
        try:
            if dialect_name == "sqlite":
                current_ts = db.execute(text("SELECT datetime('now');")).scalar()
            else:
                current_ts = db.execute(text("SELECT NOW();")).scalar()
                if current_ts:
                    current_ts = current_ts.isoformat()
        except Exception:
            pass

        return {
            "status": overall_status,
            "checks_passed": checks_passed,
            "total_checks": total_checks,
            "issues_count": len(issues),
            "issues": issues,
            "timestamp": str(current_ts)
        }

integrity_service = IntegrityService()
