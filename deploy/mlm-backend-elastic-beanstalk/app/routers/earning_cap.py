from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.earning_cycle import EarningCycle
from app.security import get_current_user, require_admin
from app.services.earning_cap_service import (
    get_user_earning_cap_overview,
    get_admin_earning_caps,
    admin_override_reset_cycle
)

router = APIRouter(prefix="/api/earning-cap", tags=["Earning Cap & Retopup"])

class AdminOverrideResetRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory audit reason for override reset")
    new_cap: Optional[float] = Field(None, gt=0, description="Optional custom earning cap limit")

@router.get("/overview")
def get_user_earning_cap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the authenticated user's current earning cycle progress, limit, status, and metrics.
    """
    try:
        return get_user_earning_cap_overview(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/list")
def get_admin_earning_cap_list(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to view and filter all user earning cycles.
    """
    try:
        return get_admin_earning_caps(
            db=db,
            status_filter=status_filter,
            search=search,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/{user_id}/history")
def get_admin_user_cycle_history(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to view all historical earning cycles for a specific user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    cycles = db.query(EarningCycle).filter(
        EarningCycle.user_id == user_id
    ).order_by(EarningCycle.cycle_number.desc()).all()
    
    return {
        'user_id': user.id,
        'user_name': user.full_name,
        'user_code': user.user_code,
        'earning_status': user.earning_status,
        'cycles': [c.to_dict() for c in cycles]
    }

@router.post("/admin/{user_id}/override-reset")
def post_admin_override_reset(
    user_id: int,
    payload: AdminOverrideResetRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to manually complete the active cycle and start a new one for a user.
    Fully audited with mandatory reason.
    """
    try:
        new_cycle = admin_override_reset_cycle(
            db=db,
            user_id=user_id,
            admin_id=admin_user.id,
            reason=payload.reason,
            new_cap=payload.new_cap
        )
        db.commit()
        return {
            'message': f"Earning cap cycle successfully reset for user {user_id}",
            'new_cycle': new_cycle.to_dict()
        }
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
