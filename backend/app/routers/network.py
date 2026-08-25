from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security import get_current_user
from app.services.mlm_service import build_binary_tree_node
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/network", tags=["network"])

@router.get("")
def get_my_tree(
    depth: int = Query(4, ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    root_node = build_binary_tree_node(db, current_user, depth=depth)
    return success_response(root_node)

@router.get("/search")
def search_network(
    q: str = Query("", min_length=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = q.strip()
    if not query:
        return success_response([])
        
    search_filter = (
        User.full_name.ilike(f"%{query}%") |
        User.user_code.ilike(f"%{query}%") |
        User.referral_code.ilike(f"%{query}%") |
        User.email.ilike(f"%{query}%")
    )
    
    users = db.query(User).filter(search_filter).limit(10).all()
    results = []
    for u in users:
        is_visible = True
        if current_user.role != 'ADMIN' and current_user.id != u.id:
            curr = u
            is_descendant = False
            while curr and curr.binary_parent_id:
                if curr.binary_parent_id == current_user.id:
                    is_descendant = True
                    break
                curr = curr.binary_parent
            if not is_descendant:
                is_visible = False
                
        if is_visible:
            results.append({
                'id': u.id,
                'user_code': u.user_code,
                'full_name': u.full_name,
                'email': u.email,
                'referral_code': u.referral_code,
                'binary_position': u.binary_position,
                'is_active': u.is_active
            })
            
    return success_response(results)

@router.get("/{user_id}")
def get_user_subtree(
    user_id: int,
    depth: int = Query(4, ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.get(User, user_id)
    if not target_user:
        return error_response("NOT_FOUND", "User not found in network.", 404)
        
    if current_user.role != 'ADMIN' and current_user.id != target_user.id:
        curr = target_user
        is_descendant = False
        while curr and curr.binary_parent_id:
            if curr.binary_parent_id == current_user.id:
                is_descendant = True
                break
            curr = curr.binary_parent
        if not is_descendant:
            return error_response("FORBIDDEN", "You can only view nodes within your own binary network.", 403)

    root_node = build_binary_tree_node(db, target_user, depth=depth)
    return success_response(root_node)
