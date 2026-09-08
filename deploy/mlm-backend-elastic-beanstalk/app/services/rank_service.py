import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.rank_config import RankConfig
from app.models.rank_achievement import RankAchievement
from app.services.wallet_service import credit_wallet
from app.services.audit_service import log_action
from app.services.time_service import time_provider

def get_rank_config(db: Session, rank_name: str) -> Optional[RankConfig]:
    return db.query(RankConfig).filter(RankConfig.rank_name == rank_name).first()

def get_all_rank_configs(db: Session) -> List[RankConfig]:
    return db.query(RankConfig).order_by(RankConfig.level.asc()).all()

def update_rank_config(
    db: Session,
    rank_name: str,
    qualification_days: Optional[int] = None,
    reward_type: Optional[str] = None,
    reward_amount: Optional[float] = None,
    is_active: Optional[bool] = None,
    admin_id: Optional[int] = None
) -> RankConfig:
    cfg = get_rank_config(db, rank_name)
    if not cfg:
        raise ValueError(f"Rank configuration for '{rank_name}' not found.")
    
    if qualification_days is not None:
        if qualification_days < 1:
            raise ValueError("Qualification days must be at least 1 day.")
        cfg.qualification_days = qualification_days
        
    if reward_type is not None:
        reward_type_upper = reward_type.upper()
        if reward_type_upper not in ['CASH', 'EV_SCOOTER']:
            raise ValueError("Invalid reward_type. Must be 'CASH' or 'EV_SCOOTER'.")
        cfg.reward_type = reward_type_upper
        
    if reward_amount is not None:
        if reward_amount < 0:
            raise ValueError("Reward amount cannot be negative.")
        cfg.reward_amount = reward_amount
        
    if is_active is not None:
        cfg.is_active = is_active
        
    cfg.updated_at = datetime.utcnow()
    db.flush()
    
    log_action(db, 'RANK_CONFIG_UPDATED', 'RankConfig', cfg.id, admin_id, {
        'rank_name': rank_name,
        'qualification_days': cfg.qualification_days,
        'reward_type': cfg.reward_type,
        'reward_amount': cfg.reward_amount,
        'is_active': cfg.is_active
    })
    
    return cfg

def get_or_create_user_rank_tracker(db: Session, user_id: int, rank_name: str) -> RankAchievement:
    """
    Retrieves or initializes a user's achievement tracker for a specific rank.
    """
    achievement = db.query(RankAchievement).filter(
        RankAchievement.user_id == user_id,
        RankAchievement.rank_name == rank_name
    ).first()
    
    if not achievement:
        cfg = get_rank_config(db, rank_name)
        if not cfg:
            raise ValueError(f"Rank config '{rank_name}' does not exist.")
            
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found.")
            
        current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
        
        # Start time is user creation time for Star, or current time for subsequent tiers
        if rank_name == 'STAR':
            started_at = user.created_at or current_ist
        else:
            # Check previous rank achievement time
            prev_rank_name = 'STAR' if rank_name == 'SUPER_STAR' else 'SUPER_STAR'
            prev_ach = db.query(RankAchievement).filter(
                RankAchievement.user_id == user_id,
                RankAchievement.rank_name == prev_rank_name,
                RankAchievement.status == 'ACHIEVED'
            ).first()
            started_at = prev_ach.achieved_at if (prev_ach and prev_ach.achieved_at) else current_ist
            
        deadline = started_at + timedelta(days=cfg.qualification_days)
        
        achievement = RankAchievement(
            user_id=user_id,
            rank_name=rank_name,
            status='IN_PROGRESS',
            qualification_started_at=started_at,
            qualification_deadline=deadline,
            achieved_at=None,
            reward_type=cfg.reward_type,
            reward_amount=cfg.reward_amount,
            reward_status='PENDING',
            qualifying_direct_ids=None
        )
        db.add(achievement)
        db.flush()
        
    return achievement

def evaluate_user_rank_progress(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Evaluates rank qualifications for a user deterministically across Level 1 (Star),
    Level 2 (Super Star), and Level 3 (VIP).
    Returns a list of triggered rank events.
    """
    user = db.get(User, user_id)
    if not user:
        return []
        
    current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
    events_triggered = []
    
    # ----------------------------------------------------
    # 1. LEVEL 1 — STAR EVALUATION
    # ----------------------------------------------------
    star_cfg = get_rank_config(db, 'STAR')
    if star_cfg and star_cfg.is_active:
        star_ach = get_or_create_user_rank_tracker(db, user_id, 'STAR')
        
        if star_ach.status == 'IN_PROGRESS':
            # Check active direct sponsored users created/activated within the qualification window
            directs = db.query(User).filter(
                User.sponsor_id == user_id,
                User.is_active == True,
                User.created_at <= star_ach.qualification_deadline
            ).order_by(User.created_at.asc()).all()
            
            if len(directs) >= star_cfg.required_directs:
                qualifying_directs = directs[:star_cfg.required_directs]
                star_ach.status = 'ACHIEVED'
                star_ach.achieved_at = current_ist
                star_ach.qualifying_direct_ids = json.dumps([d.id for d in qualifying_directs])
                if user.current_rank not in ['SUPER_STAR', 'VIP']:
                    user.current_rank = 'STAR'
                
                # Issue ₹2,100 reward via wallet ledger
                txn = credit_wallet(
                    db=db,
                    user_id=user.id,
                    amount=star_ach.reward_amount,
                    category='RANK_REWARD',
                    description=f"Level 1 Star Rank Achievement Award (₹{star_ach.reward_amount:,.0f})",
                    reference_id=f"RANK-STAR-{star_ach.id}"
                )
                star_ach.reward_status = 'CREDITED'
                star_ach.reward_transaction_id = txn.id
                db.flush()
                
                log_action(db, 'RANK_ACHIEVED', 'RankAchievement', star_ach.id, user.id, {
                    'rank': 'STAR',
                    'award': star_ach.reward_amount,
                    'qualifying_direct_ids': [d.id for d in qualifying_directs]
                })
                
                events_triggered.append({
                    'type': 'RANK_PROMOTED',
                    'rank': 'STAR',
                    'user_id': user.id,
                    'user_name': user.full_name,
                    'award': star_ach.reward_amount,
                    'reward_type': star_ach.reward_type
                })
                
                # Initialize Super Star tracker immediately upon Star promotion
                get_or_create_user_rank_tracker(db, user_id, 'SUPER_STAR')
            elif current_ist > star_ach.qualification_deadline:
                star_ach.status = 'EXPIRED'
                star_ach.reward_status = 'EXPIRED'
                db.flush()
                
    # ----------------------------------------------------
    # 2. LEVEL 2 — SUPER STAR EVALUATION
    # ----------------------------------------------------
    super_star_cfg = get_rank_config(db, 'SUPER_STAR')
    star_ach = db.query(RankAchievement).filter(
        RankAchievement.user_id == user_id,
        RankAchievement.rank_name == 'STAR',
        RankAchievement.status == 'ACHIEVED'
    ).first()
    
    if (star_ach or user.current_rank in ['STAR', 'SUPER_STAR', 'VIP']) and super_star_cfg and super_star_cfg.is_active:
        super_star_ach = get_or_create_user_rank_tracker(db, user_id, 'SUPER_STAR')
        
        if super_star_ach.status == 'IN_PROGRESS':
            # Check user's direct sponsored members who have achieved STAR rank
            # on or before user's Super Star deadline
            direct_star_users = db.query(User).join(
                RankAchievement, RankAchievement.user_id == User.id
            ).filter(
                User.sponsor_id == user_id,
                RankAchievement.rank_name == 'STAR',
                RankAchievement.status == 'ACHIEVED',
                RankAchievement.achieved_at <= super_star_ach.qualification_deadline
            ).order_by(RankAchievement.achieved_at.asc()).all()
            
            if len(direct_star_users) >= super_star_cfg.required_directs:
                qualifying_direct_stars = direct_star_users[:super_star_cfg.required_directs]
                super_star_ach.status = 'ACHIEVED'
                super_star_ach.achieved_at = current_ist
                super_star_ach.qualifying_direct_ids = json.dumps([d.id for d in qualifying_direct_stars])
                if user.current_rank != 'VIP':
                    user.current_rank = 'SUPER_STAR'
                
                # Issue ₹5,100 reward via wallet ledger
                txn = credit_wallet(
                    db=db,
                    user_id=user.id,
                    amount=super_star_ach.reward_amount,
                    category='RANK_REWARD',
                    description=f"Level 2 Super Star Rank Achievement Award (₹{super_star_ach.reward_amount:,.0f})",
                    reference_id=f"RANK-SUPER_STAR-{super_star_ach.id}"
                )
                super_star_ach.reward_status = 'CREDITED'
                super_star_ach.reward_transaction_id = txn.id
                db.flush()
                
                log_action(db, 'RANK_ACHIEVED', 'RankAchievement', super_star_ach.id, user.id, {
                    'rank': 'SUPER_STAR',
                    'award': super_star_ach.reward_amount,
                    'qualifying_direct_ids': [d.id for d in qualifying_direct_stars]
                })
                
                events_triggered.append({
                    'type': 'RANK_PROMOTED',
                    'rank': 'SUPER_STAR',
                    'user_id': user.id,
                    'user_name': user.full_name,
                    'award': super_star_ach.reward_amount,
                    'reward_type': super_star_ach.reward_type
                })
                
                # Initialize VIP tracker immediately upon Super Star promotion
                get_or_create_user_rank_tracker(db, user_id, 'VIP')
            elif current_ist > super_star_ach.qualification_deadline:
                super_star_ach.status = 'EXPIRED'
                super_star_ach.reward_status = 'EXPIRED'
                db.flush()
                
    # ----------------------------------------------------
    # 3. LEVEL 3 — VIP EVALUATION
    # ----------------------------------------------------
    vip_cfg = get_rank_config(db, 'VIP')
    super_star_ach = db.query(RankAchievement).filter(
        RankAchievement.user_id == user_id,
        RankAchievement.rank_name == 'SUPER_STAR',
        RankAchievement.status == 'ACHIEVED'
    ).first()
    
    if (super_star_ach or user.current_rank in ['SUPER_STAR', 'VIP']) and vip_cfg and vip_cfg.is_active:
        vip_ach = get_or_create_user_rank_tracker(db, user_id, 'VIP')
        
        if vip_ach.status == 'IN_PROGRESS':
            # Check user's direct sponsored members who have achieved SUPER_STAR rank
            # on or before user's VIP deadline
            direct_super_star_users = db.query(User).join(
                RankAchievement, RankAchievement.user_id == User.id
            ).filter(
                User.sponsor_id == user_id,
                RankAchievement.rank_name == 'SUPER_STAR',
                RankAchievement.status == 'ACHIEVED',
                RankAchievement.achieved_at <= vip_ach.qualification_deadline
            ).order_by(RankAchievement.achieved_at.asc()).all()
            
            if len(direct_super_star_users) >= vip_cfg.required_directs:
                qualifying_vip_directs = direct_super_star_users[:vip_cfg.required_directs]
                vip_ach.status = 'ACHIEVED'
                vip_ach.achieved_at = current_ist
                vip_ach.qualifying_direct_ids = json.dumps([d.id for d in qualifying_vip_directs])
                user.current_rank = 'VIP'
                
                # Sync configured reward type from active VIP config
                vip_ach.reward_type = vip_cfg.reward_type
                vip_ach.reward_amount = vip_cfg.reward_amount
                
                if vip_cfg.reward_type == 'CASH':
                    # Issue ₹51,000 Cash reward via wallet ledger
                    txn = credit_wallet(
                        db=db,
                        user_id=user.id,
                        amount=vip_ach.reward_amount,
                        category='RANK_REWARD',
                        description=f"Level 3 VIP Rank Achievement Award (₹{vip_ach.reward_amount:,.0f} Cash)",
                        reference_id=f"RANK-VIP-{vip_ach.id}"
                    )
                    vip_ach.reward_status = 'CREDITED'
                    vip_ach.reward_transaction_id = txn.id
                else:
                    # Non-cash reward: EV Scooter
                    vip_ach.reward_status = 'PENDING_FULFILLMENT'
                    vip_ach.reward_transaction_id = None
                    
                db.flush()
                
                log_action(db, 'RANK_ACHIEVED', 'RankAchievement', vip_ach.id, user.id, {
                    'rank': 'VIP',
                    'reward_type': vip_ach.reward_type,
                    'award': vip_ach.reward_amount,
                    'qualifying_direct_ids': [d.id for d in qualifying_vip_directs]
                })
                
                events_triggered.append({
                    'type': 'RANK_PROMOTED',
                    'rank': 'VIP',
                    'user_id': user.id,
                    'user_name': user.full_name,
                    'award': vip_ach.reward_amount,
                    'reward_type': vip_ach.reward_type
                })
            elif current_ist > vip_ach.qualification_deadline:
                vip_ach.status = 'EXPIRED'
                vip_ach.reward_status = 'EXPIRED'
                db.flush()
                
    return events_triggered

def evaluate_ranks_on_user_activation(db: Session, user_id: int):
    """
    Called when a user activates a package.
    Evaluates the sponsor's rank progress and cascades upward if sponsor achieves promotion.
    """
    user = db.get(User, user_id)
    if not user or not user.sponsor_id:
        return
        
    current_sponsor_id = user.sponsor_id
    visited = set()
    
    while current_sponsor_id and current_sponsor_id not in visited:
        visited.add(current_sponsor_id)
        events = evaluate_user_rank_progress(db, current_sponsor_id)
        
        # If no promotion occurred for this sponsor, upward cascade stops
        if not events:
            break
            
        sponsor = db.get(User, current_sponsor_id)
        current_sponsor_id = sponsor.sponsor_id if sponsor else None

def get_user_rank_overview(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Returns comprehensive rank progress and reward status for a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found.")
        
    current_ist = time_provider.get_current_ist_time(db).replace(tzinfo=None)
    
    # Ensure active trackers exist for eligible tiers
    get_or_create_user_rank_tracker(db, user_id, 'STAR')
    if user.current_rank in ['STAR', 'SUPER_STAR', 'VIP']:
        get_or_create_user_rank_tracker(db, user_id, 'SUPER_STAR')
    if user.current_rank in ['SUPER_STAR', 'VIP']:
        get_or_create_user_rank_tracker(db, user_id, 'VIP')
        
    # Evaluate live progress before building response
    evaluate_user_rank_progress(db, user_id)
    
    achievements = db.query(RankAchievement).filter(RankAchievement.user_id == user_id).all()
    ach_map = {a.rank_name: a for a in achievements}
    configs = get_all_rank_configs(db)
    
    tiers = []
    
    for cfg in configs:
        ach = ach_map.get(cfg.rank_name)
        
        status = 'LOCKED'
        started_at = None
        deadline = None
        achieved_at = None
        remaining_seconds = 0
        is_expired = False
        reward_status = 'PENDING'
        reward_type = cfg.reward_type
        reward_amount = cfg.reward_amount
        current_count = 0
        qualifying_members = []
        
        if ach:
            status = ach.status
            started_at = ach.qualification_started_at.isoformat() if ach.qualification_started_at else None
            deadline = ach.qualification_deadline.isoformat() if ach.qualification_deadline else None
            achieved_at = ach.achieved_at.isoformat() if ach.achieved_at else None
            reward_status = ach.reward_status
            reward_type = ach.reward_type
            reward_amount = ach.reward_amount
            
            if ach.qualification_deadline:
                diff = (ach.qualification_deadline - current_ist).total_seconds()
                remaining_seconds = max(0, int(diff))
                is_expired = diff <= 0 and ach.status != 'ACHIEVED'
                
            # Parse contributing members if already achieved
            if ach.qualifying_direct_ids:
                try:
                    q_ids = json.loads(ach.qualifying_direct_ids)
                    q_users = db.query(User).filter(User.id.in_(q_ids)).all()
                    qualifying_members = [{
                        'id': u.id,
                        'full_name': u.full_name,
                        'user_code': u.user_code,
                        'current_rank': u.current_rank
                    } for u in q_users]
                    current_count = len(qualifying_members)
                except Exception:
                    pass
            elif ach.status == 'IN_PROGRESS':
                # Calculate live in-progress contributing directs
                if cfg.rank_name == 'STAR':
                    directs = db.query(User).filter(
                        User.sponsor_id == user_id,
                        User.is_active == True,
                        User.created_at <= ach.qualification_deadline
                    ).all()
                    current_count = len(directs)
                    qualifying_members = [{
                        'id': u.id,
                        'full_name': u.full_name,
                        'user_code': u.user_code,
                        'created_at': u.created_at.isoformat() if u.created_at else None
                    } for u in directs]
                elif cfg.rank_name == 'SUPER_STAR':
                    direct_stars = db.query(User).join(
                        RankAchievement, RankAchievement.user_id == User.id
                    ).filter(
                        User.sponsor_id == user_id,
                        RankAchievement.rank_name == 'STAR',
                        RankAchievement.status == 'ACHIEVED',
                        RankAchievement.achieved_at <= ach.qualification_deadline
                    ).all()
                    current_count = len(direct_stars)
                    qualifying_members = [{
                        'id': u.id,
                        'full_name': u.full_name,
                        'user_code': u.user_code,
                        'current_rank': u.current_rank
                    } for u in direct_stars]
                elif cfg.rank_name == 'VIP':
                    direct_super_stars = db.query(User).join(
                        RankAchievement, RankAchievement.user_id == User.id
                    ).filter(
                        User.sponsor_id == user_id,
                        RankAchievement.rank_name == 'SUPER_STAR',
                        RankAchievement.status == 'ACHIEVED',
                        RankAchievement.achieved_at <= ach.qualification_deadline
                    ).all()
                    current_count = len(direct_super_stars)
                    qualifying_members = [{
                        'id': u.id,
                        'full_name': u.full_name,
                        'user_code': u.user_code,
                        'current_rank': u.current_rank
                    } for u in direct_super_stars]
        else:
            # If not yet tracked, calculate whether previous rank is achieved to determine if locked
            if cfg.rank_name == 'SUPER_STAR' and user.current_rank not in ['STAR', 'SUPER_STAR', 'VIP']:
                status = 'LOCKED'
            elif cfg.rank_name == 'VIP' and user.current_rank not in ['SUPER_STAR', 'VIP']:
                status = 'LOCKED'
                
        progress_percentage = min(100, int((current_count / cfg.required_directs) * 100)) if cfg.required_directs > 0 else 0
        
        tiers.append({
            'rank_name': cfg.rank_name,
            'display_name': cfg.display_name,
            'level': cfg.level,
            'required_directs': cfg.required_directs,
            'qualification_days': cfg.qualification_days,
            'reward_type': reward_type,
            'reward_amount': reward_amount,
            'status': status,
            'current_count': current_count,
            'progress_percentage': progress_percentage,
            'qualification_started_at': started_at,
            'qualification_deadline': deadline,
            'achieved_at': achieved_at,
            'remaining_seconds': remaining_seconds,
            'is_expired': is_expired,
            'reward_status': reward_status,
            'qualifying_members': qualifying_members
        })
        
    return {
        'user_id': user.id,
        'full_name': user.full_name,
        'user_code': user.user_code,
        'current_rank': user.current_rank or 'DISTRIBUTOR',
        'server_time': current_ist.isoformat(),
        'tiers': tiers
    }

def get_admin_rank_achievements(
    db: Session,
    rank_name: Optional[str] = None,
    status: Optional[str] = None,
    reward_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    query = db.query(RankAchievement).join(User, RankAchievement.user_id == User.id)
    
    if rank_name and rank_name != 'ALL':
        query = query.filter(RankAchievement.rank_name == rank_name)
    if status and status != 'ALL':
        query = query.filter(RankAchievement.status == status)
    if reward_status and reward_status != 'ALL':
        query = query.filter(RankAchievement.reward_status == reward_status)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(search_pattern)) | 
            (User.user_code.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )
        
    total = query.count()
    items = query.order_by(desc(RankAchievement.created_at)).offset(offset).limit(limit).all()
    
    return {
        'total': total,
        'items': [item.to_dict() for item in items]
    }

def update_achievement_fulfillment(
    db: Session,
    achievement_id: int,
    reward_status: str,
    admin_notes: Optional[str] = None,
    admin_id: Optional[int] = None
) -> RankAchievement:
    ach = db.get(RankAchievement, achievement_id)
    if not ach:
        raise ValueError(f"Achievement {achievement_id} not found.")
        
    allowed_statuses = ['PENDING', 'CREDITED', 'PENDING_FULFILLMENT', 'FULFILLED', 'REJECTED']
    if reward_status not in allowed_statuses:
        raise ValueError(f"Invalid reward status '{reward_status}'. Allowed: {allowed_statuses}")
        
    ach.reward_status = reward_status
    if admin_notes is not None:
        ach.admin_notes = admin_notes
    ach.updated_at = datetime.utcnow()
    db.flush()
    
    log_action(db, 'ACHIEVEMENT_FULFILLMENT_UPDATED', 'RankAchievement', ach.id, admin_id, {
        'user_id': ach.user_id,
        'rank_name': ach.rank_name,
        'reward_status': reward_status,
        'admin_notes': admin_notes
    })
    
    return ach
