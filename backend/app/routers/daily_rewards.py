from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security import get_current_user, require_admin
from app.services.daily_reward_service import daily_reward_service, SettlementTimingError

router = APIRouter(prefix="/api/daily-rewards", tags=["Daily Package Refund"])

class SettleDailyRewardsRequest(BaseModel):
    business_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Business date in YYYY-MM-DD format (defaults to current IST date)")
    force: bool = Field(False, description="Emergency admin override to bypass 07:00 AM cutoff for testing/backfill")

@router.get("/overview")
def get_user_daily_reward_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the authenticated user's current Daily Package Refund cycle,
    active daily reward rate, completed pair count, refund progress, and next credit countdown.
    """
    try:
        return daily_reward_service.get_user_daily_reward_overview(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/cycles")
def get_admin_daily_reward_cycles(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to view, search, filter, and paginate Daily Package Refund cycles.
    """
    try:
        return daily_reward_service.get_admin_daily_reward_cycles(
            db=db,
            status_filter=status_filter,
            search=search,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/transactions")
def get_admin_daily_reward_transactions(
    cycle_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    business_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to view daily refund transaction audit logs.
    """
    try:
        return daily_reward_service.get_admin_daily_reward_transactions(
            db=db,
            cycle_id=cycle_id,
            user_id=user_id,
            business_date=business_date,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/settle")
def settle_daily_rewards(
    payload: Optional[SettleDailyRewardsRequest] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to execute daily package refund settlement for all active cycles.
    Protected by 07:00 AM IST cutoff check and strict idempotency.
    """
    b_date = None
    force = False
    if payload:
        force = payload.force
        if payload.business_date:
            try:
                b_date = datetime.strptime(payload.business_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid business_date format. Must be YYYY-MM-DD.")
    try:
        result = daily_reward_service.settle_daily_rewards(db, business_date=b_date, force=force)
        db.commit()
        return result
    except SettlementTimingError as te:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(te))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Settlement failed: {str(e)}")
