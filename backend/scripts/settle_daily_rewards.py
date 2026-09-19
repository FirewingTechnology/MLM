"""
Daily Package Refund / Daily Reward Settlement Script
Can be run via cron / AWS EventBridge / task scheduler at or after 07:00 AM IST.

Usage:
    python -m scripts.settle_daily_rewards [--date YYYY-MM-DD] [--force]
"""
import sys
import os
import argparse
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.daily_reward_service import daily_reward_service, SettlementTimingError

def main():
    parser = argparse.ArgumentParser(description="Settle Daily Package Refunds for active cycles.")
    parser.add_argument("--date", type=str, help="Target business date in YYYY-MM-DD format (default: today IST).")
    parser.add_argument("--force", action="store_true", help="Force settlement execution even before 07:00 AM IST (for test/manual override).")
    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Expected YYYY-MM-DD.")
            sys.exit(1)

    db = SessionLocal()
    try:
        print(f"Starting Daily Package Refund settlement (force={args.force})...")
        summary = daily_reward_service.settle_daily_rewards(db, business_date=target_date, force=args.force)
        db.commit()
        print(f"Settlement finished successfully for business date: {summary['business_date']}")
        print(f"  - Active Cycles:   {summary['total_active_cycles']}")
        print(f"  - Processed:       {summary['processed_count']}")
        print(f"  - Credited:        {summary['credited_count']}")
        print(f"  - Skipped:         {summary['skipped_count']}")
        print(f"  - Total Credited:  ₹{summary['total_credited_amount']:,.2f}")
    except SettlementTimingError as ste:
        print(f"Notice: {ste}")
        sys.exit(0)
    except Exception as e:
        db.rollback()
        print(f"CRITICAL: Settlement failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
