from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.package import Package
from app.utils.responses import success_response

router = APIRouter(prefix="/api/packages", tags=["packages"])

@router.get("")
def get_packages(db: Session = Depends(get_db)):
    packages = db.query(Package).filter(Package.is_active == True).all()
    return success_response([p.to_dict() for p in packages])
