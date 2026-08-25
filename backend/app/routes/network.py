from flask import Blueprint, request
from app.extensions import db
from app.models.user import User
from app.services.mlm_service import build_binary_tree_node
from app.utils.responses import success_response, error_response
from app.middleware.auth import token_required

network_bp = Blueprint('network', __name__, url_prefix='/api/network')

@network_bp.route('', methods=['GET'])
@token_required
def get_my_tree(current_user):
    depth = request.args.get('depth', 4, type=int)
    root_node = build_binary_tree_node(current_user, depth=depth)
    return success_response(root_node)

@network_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user_subtree(current_user, user_id):
    depth = request.args.get('depth', 4, type=int)
    target_user = db.session.get(User, user_id)
    if not target_user:
        return error_response("NOT_FOUND", "User not found in network.", 404)
        
    # Check if target_user is in current_user's subtree or current_user is ADMIN
    if current_user.role != 'ADMIN' and current_user.id != target_user.id:
        # Traverse upward from target_user to check if current_user is an ancestor
        curr = target_user
        is_descendant = False
        while curr and curr.binary_parent_id:
            if curr.binary_parent_id == current_user.id:
                is_descendant = True
                break
            curr = curr.binary_parent
        if not is_descendant:
            return error_response("FORBIDDEN", "You can only view nodes within your own binary network.", 403)

    root_node = build_binary_tree_node(target_user, depth=depth)
    return success_response(root_node)

@network_bp.route('/search', methods=['GET'])
@token_required
def search_network(current_user):
    query = request.args.get('q', '').strip()
    if not query:
        return success_response([])
        
    # Search users matching name, code, email, mobile
    search_filter = (
        User.full_name.ilike(f"%{query}%") |
        User.user_code.ilike(f"%{query}%") |
        User.referral_code.ilike(f"%{query}%") |
        User.email.ilike(f"%{query}%")
    )
    
    users = User.query.filter(search_filter).limit(10).all()
    results = []
    for u in users:
        # Check permissions if not admin
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
