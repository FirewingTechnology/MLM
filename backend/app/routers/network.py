from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.slot_settlement import SlotSettlement
from app.models.volume_ledger import VolumeLedger
from app.security import get_current_user
from app.services.mlm_service import build_binary_tree_node
from app.services.time_service import time_provider
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/network", tags=["network"])

@router.get("")
def get_my_tree(
    depth: int = Query(4, ge=1, le=5),
    view: str = Query("network"),
    slot_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not slot_id:
        slot_info = time_provider.get_current_slot_info(db)
        slot_id = slot_info.slot_id

    root_node = build_binary_tree_node(
        db=db,
        user=current_user,
        depth=depth,
        view_mode=view,
        slot_id=slot_id
    )
    return success_response(root_node)

@router.get("/settlements")
def get_my_settlements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns past slot settlements for current user."""
    query = db.query(SlotSettlement).filter(SlotSettlement.user_id == current_user.id)
    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(SlotSettlement.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [s.to_dict() for s in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

@router.get("/volume-ledger")
def get_my_volume_ledger(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    side: Optional[str] = Query(None),
    slot_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns volume ledger entries contributing to current user's matching balance."""
    query = db.query(VolumeLedger).filter(VolumeLedger.ancestor_user_id == current_user.id)
    if side:
        query = query.filter(VolumeLedger.side == side.strip().upper())
    if slot_id:
        query = query.filter(VolumeLedger.slot_id == slot_id.strip())

    total = query.count()
    offset = (page - 1) * per_page
    items = query.order_by(VolumeLedger.id.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return success_response({
        'items': [v.to_dict() for v in items],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    })

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

@router.get("/members")
def get_network_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns ordered list of all accessible members in user's downline for sequential next/previous navigation.
    """
    from collections import deque

    members = []
    if current_user.role == 'ADMIN':
        # Admin can view all users
        all_users = db.query(User).order_by(User.id.asc()).all()
        for u in all_users:
            members.append({
                'id': u.id,
                'user_code': u.user_code,
                'full_name': u.full_name,
                'email': u.email,
                'role': u.role,
                'binary_position': u.binary_position,
                'binary_parent_id': u.binary_parent_id,
                'is_active': u.is_active
            })
    else:
        # Traverse BFS downline starting from current_user
        queue = deque([current_user])
        while queue:
            curr = queue.popleft()
            members.append({
                'id': curr.id,
                'user_code': curr.user_code,
                'full_name': curr.full_name,
                'email': curr.email,
                'role': curr.role,
                'binary_position': curr.binary_position,
                'binary_parent_id': curr.binary_parent_id,
                'is_active': curr.is_active
            })
            children = db.query(User).filter(User.binary_parent_id == curr.id).order_by(User.binary_position.asc()).all()
            for child in children:
                queue.append(child)

    return success_response(members)

@router.get("/{user_id}")
def get_user_subtree(
    user_id: int,
    depth: int = Query(4, ge=1, le=5),
    view: str = Query("network"),
    slot_id: Optional[str] = Query(None),
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

    if not slot_id:
        slot_info = time_provider.get_current_slot_info(db)
        slot_id = slot_info.slot_id

    root_node = build_binary_tree_node(
        db=db,
        user=target_user,
        depth=depth,
        view_mode=view,
        slot_id=slot_id
    )
    return success_response(root_node)
