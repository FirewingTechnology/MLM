from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.time_service import time_provider
from app.utils.responses import success_response

router = APIRouter(prefix="/api/time", tags=["time"])

@router.get("/current")
def get_current_time(db: Session = Depends(get_db)):
    """Returns the current IST slot information, countdown, and active mode (REAL or DEMO)."""
    slot_info = time_provider.get_current_slot_info(db)
    return success_response(slot_info.to_dict())
