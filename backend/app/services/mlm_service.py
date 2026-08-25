from collections import deque
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.volume import BinaryVolume
from app.models.purchase import Purchase

class MLMPlacementError(Exception):
    pass

def resolve_sponsor_by_code(db: Session, referral_code: str) -> User:
    if not referral_code:
        return None
    return db.query(User).filter(User.referral_code == referral_code.strip().upper()).first()

def get_or_create_binary_volume(db: Session, user_id: int) -> BinaryVolume:
    vol = db.query(BinaryVolume).filter(BinaryVolume.user_id == user_id).first()
    if not vol:
        vol = BinaryVolume(
            user_id=user_id,
            accumulated_left_bv=0.0,
            accumulated_right_bv=0.0,
            carry_left_bv=0.0,
            carry_right_bv=0.0,
            matched_bv=0.0,
            personal_bv=0.0
        )
        db.add(vol)
        db.flush()
    return vol

def validate_binary_placement(db: Session, parent_id: int, position: str) -> bool:
    if position not in ('LEFT', 'RIGHT'):
        raise MLMPlacementError("Binary position must be either 'LEFT' or 'RIGHT'.")
        
    parent = db.get(User, parent_id)
    if not parent:
        raise MLMPlacementError(f"Parent user ID {parent_id} does not exist.")
        
    # Check if this position is already occupied
    occupied = db.query(User).filter(
        User.binary_parent_id == parent_id,
        User.binary_position == position
    ).first()
    
    if occupied:
        raise MLMPlacementError(f"Position '{position}' under {parent.full_name} ({parent.user_code}) is already occupied by {occupied.full_name}.")
        
    return True

def auto_place_in_binary_tree(db: Session, root_user_id: int, preferred_leg: str = None) -> tuple[int, str]:
    root = db.get(User, root_user_id)
    if not root:
        raise MLMPlacementError("Root node for placement not found.")
        
    # If preferred leg is explicitly LEFT or RIGHT, search down that leg first
    queue = deque([root])
    
    while queue:
        current = queue.popleft()
        
        left_child = db.query(User).filter(User.binary_parent_id == current.id, User.binary_position == 'LEFT').first()
        right_child = db.query(User).filter(User.binary_parent_id == current.id, User.binary_position == 'RIGHT').first()
        
        if preferred_leg == 'LEFT':
            if not left_child:
                return current.id, 'LEFT'
            if not right_child:
                return current.id, 'RIGHT'
        elif preferred_leg == 'RIGHT':
            if not right_child:
                return current.id, 'RIGHT'
            if not left_child:
                return current.id, 'LEFT'
        else:
            if not left_child:
                return current.id, 'LEFT'
            if not right_child:
                return current.id, 'RIGHT'
                
        if left_child:
            queue.append(left_child)
        if right_child:
            queue.append(right_child)
            
    raise MLMPlacementError("Could not find an available placement spot in binary tree.")

def get_binary_ancestors(db: Session, user_id: int) -> list[tuple[User, str]]:
    ancestors = []
    current = db.get(User, user_id)
    
    visited = set()
    while current and current.binary_parent_id:
        if current.id in visited:
            break
        visited.add(current.id)
        
        parent = db.get(User, current.binary_parent_id)
        if not parent:
            break
        position = current.binary_position
        ancestors.append((parent, position))
        current = parent
        
    return ancestors

def count_total_network_members(db: Session, user_id: int) -> int:
    count = 0
    queue = deque([user_id])
    while queue:
        curr_id = queue.popleft()
        children = db.query(User).filter(User.binary_parent_id == curr_id).all()
        count += len(children)
        for child in children:
            queue.append(child.id)
    return count

def build_binary_tree_node(db: Session, user: User, depth: int = 3, current_depth: int = 1) -> dict:
    if not user:
        return None
        
    vol = get_or_create_binary_volume(db, user.id)
    
    # Left and Right immediate children
    left_child = db.query(User).filter(User.binary_parent_id == user.id, User.binary_position == 'LEFT').first()
    right_child = db.query(User).filter(User.binary_parent_id == user.id, User.binary_position == 'RIGHT').first()
    
    direct_count = db.query(User).filter(User.sponsor_id == user.id).count()
    
    # Get active package name if any
    last_purchase = db.query(Purchase).filter(Purchase.user_id == user.id).order_by(Purchase.created_at.desc()).first()
    
    node = {
        'id': user.id,
        'user_code': user.user_code,
        'full_name': user.full_name,
        'email': user.email,
        'referral_code': user.referral_code,
        'role': user.role,
        'is_active': user.is_active,
        'active_package': last_purchase.package.name if (last_purchase and last_purchase.package) else ('Active Package' if user.is_active else 'No Package'),
        'sponsor_id': user.sponsor_id,
        'sponsor_name': user.sponsor.full_name if user.sponsor else None,
        'sponsor_code': user.sponsor.user_code if user.sponsor else None,
        'binary_parent_id': user.binary_parent_id,
        'binary_parent_name': user.binary_parent.full_name if user.binary_parent else None,
        'binary_position': user.binary_position,
        'direct_referrals': direct_count,
        'personal_bv': vol.personal_bv,
        'accumulated_left_bv': vol.accumulated_left_bv,
        'accumulated_right_bv': vol.accumulated_right_bv,
        'carry_left_bv': vol.carry_left_bv,
        'carry_right_bv': vol.carry_right_bv,
        'matched_bv': vol.matched_bv,
        'left': None,
        'right': None
    }
    
    if current_depth < depth:
        node['left'] = build_binary_tree_node(db, left_child, depth, current_depth + 1) if left_child else None
        node['right'] = build_binary_tree_node(db, right_child, depth, current_depth + 1) if right_child else None
        
    return node
