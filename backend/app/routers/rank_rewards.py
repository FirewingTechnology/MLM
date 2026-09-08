from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import get_current_user, get_current_admin
from app.utils.responses import success_response, error_response
from app.services.rank_service import (
    get_all_rank_configs,
    get_rank_config,
    update_rank_config,
    get_user_rank_overview,
    get_admin_rank_achievements,
    update_achievement_fulfillment,
    evaluate_user_rank_progress
)

router = APIRouter(tags=["rank_rewards"])

class UpdateRankConfigRequest(BaseModel):
    qualification_days: Optional[int] = Field(None, ge=1)
    reward_type: Optional[str] = None
    reward_amount: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[bool] = None

class UpdateFulfillmentRequest(BaseModel):
    reward_status: str
    admin_notes: Optional[str] = None

# =========================================================================
# USER ENDPOINTS
# =========================================================================

@router.get("/api/rank-rewards/overview")
def get_rank_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        overview = get_user_rank_overview(db, current_user.id)
        return success_response(overview)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "RANK_OVERVIEW_ERROR", "message": str(e)}
        )

# =========================================================================
# ADMIN ENDPOINTS
# =========================================================================

@router.get("/api/admin/rank-rewards/config")
def get_admin_rank_configs(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_all_rank_configs(db)
    return success_response([c.to_dict() for c in configs])

@router.put("/api/admin/rank-rewards/config/{rank_name}")
def update_admin_rank_config(
    rank_name: str,
    payload: UpdateRankConfigRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        updated_cfg = update_rank_config(
            db=db,
            rank_name=rank_name.strip().upper(),
            qualification_days=payload.qualification_days,
            reward_type=payload.reward_type,
            reward_amount=payload.reward_amount,
            is_active=payload.is_active,
            admin_id=current_admin.id
        )
        db.commit()
        return success_response(updated_cfg.to_dict(), message="Rank configuration successfully updated")
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CONFIG", "message": str(e)}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CONFIG_UPDATE_FAILED", "message": str(e)}
        )

@router.get("/api/admin/rank-rewards/achievements")
def get_admin_achievements(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    rank_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    reward_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    result = get_admin_rank_achievements(
        db=db,
        rank_name=rank_name,
        status=status_filter,
        reward_status=reward_status,
        search=search,
        limit=per_page,
        offset=offset
    )
    pages = (result['total'] + per_page - 1) // per_page if result['total'] > 0 else 1
    return success_response({
        'items': result['items'],
        'total': result['total'],
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.put("/api/admin/rank-rewards/achievements/{achievement_id}/fulfillment")
def update_fulfillment(
    achievement_id: int,
    payload: UpdateFulfillmentRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        ach = update_achievement_fulfillment(
            db=db,
            achievement_id=achievement_id,
            reward_status=payload.reward_status.strip().upper(),
            admin_notes=payload.admin_notes,
            admin_id=current_admin.id
        )
        db.commit()
        return success_response(ach.to_dict(), message="Fulfillment status updated successfully")
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FULFILLMENT_STATUS", "message": str(e)}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "FULFILLMENT_UPDATE_FAILED", "message": str(e)}
        )

@router.post("/api/admin/rank-rewards/evaluate/{user_id}")
def evaluate_user_ranks_manually(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        events = evaluate_user_rank_progress(db, user_id)
        db.commit()
        overview = get_user_rank_overview(db, user_id)
        return success_response({
            'events_triggered': events,
            'overview': overview
        }, message=f"Evaluated ranks for user {user_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EVALUATION_ERROR", "message": str(e)}
        )
