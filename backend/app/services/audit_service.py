from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def log_action(db: Session, action: str, entity_type: str, entity_id=None, user_id=None, details=None):
    try:
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            user_id=user_id,
            _details=None
        )
        if details:
            log.details = details
        db.add(log)
        db.flush()
        return log
    except Exception:
        return None
