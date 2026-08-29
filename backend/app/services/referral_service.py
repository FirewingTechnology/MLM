import secrets
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.referral_token import ReferralToken
from app.services.mlm_service import resolve_sponsor_by_code

def get_or_create_referral_token(db: Session, sponsor_id: int, placement_side: str) -> ReferralToken:
    """
    Retrieves or generates a permanent, cryptographically unique referral token
    locked to sponsor_id and placement_side ('LEFT' or 'RIGHT').
    """
    side = placement_side.strip().upper()
    if side not in ('LEFT', 'RIGHT'):
        raise ValueError("Placement side must be 'LEFT' or 'RIGHT'.")

    sponsor = db.get(User, sponsor_id)
    if not sponsor:
        raise ValueError(f"Sponsor user ID {sponsor_id} not found.")

    token_rec = db.query(ReferralToken).filter(
        ReferralToken.sponsor_user_id == sponsor_id,
        ReferralToken.placement_side == side,
        ReferralToken.is_active == True
    ).first()

    if token_rec:
        return token_rec

    # Generate a secure token with sponsor referral code prefix
    random_part = secrets.token_hex(6).upper()
    token_str = f"REF-{sponsor.referral_code}-{side}-{random_part}"

    # Ensure uniqueness
    while db.query(ReferralToken).filter(ReferralToken.token == token_str).first():
        random_part = secrets.token_hex(6).upper()
        token_str = f"REF-{sponsor.referral_code}-{side}-{random_part}"

    token_rec = ReferralToken(
        token=token_str,
        sponsor_user_id=sponsor_id,
        placement_side=side,
        is_active=True
    )
    db.add(token_rec)
    db.commit()
    db.refresh(token_rec)
    return token_rec

def get_user_referral_links(db: Session, user: User) -> dict:
    """Returns the LEFT and RIGHT locked referral tokens and info for a user."""
    left_token = get_or_create_referral_token(db, user.id, 'LEFT')
    right_token = get_or_create_referral_token(db, user.id, 'RIGHT')

    return {
        'left': {
            'token': left_token.token,
            'placement_side': 'LEFT',
            'sponsor_name': user.full_name,
            'sponsor_code': user.user_code,
            'referral_code': user.referral_code
        },
        'right': {
            'token': right_token.token,
            'placement_side': 'RIGHT',
            'sponsor_name': user.full_name,
            'sponsor_code': user.user_code,
            'referral_code': user.referral_code
        }
    }

def validate_referral_input(db: Session, token_or_code: str) -> dict:
    """
    Validates a referral token or legacy referral code.
    Returns:
      {
        'valid': bool,
        'sponsor_name': str,
        'sponsor_code': str,
        'referral_code': str,
        'placement_side': 'LEFT' | 'RIGHT' | None,
        'is_locked': bool,
        'token': str | None
      }
    """
    if not token_or_code or not token_or_code.strip():
        return {'valid': False, 'error': 'Referral identifier is empty.'}

    clean_str = token_or_code.strip()

    # 1. First, try matching exact ReferralToken
    token_rec = db.query(ReferralToken).filter(
        ReferralToken.token == clean_str,
        ReferralToken.is_active == True
    ).first()

    if token_rec and token_rec.sponsor:
        return {
            'valid': True,
            'sponsor_name': token_rec.sponsor.full_name,
            'sponsor_code': token_rec.sponsor.user_code,
            'referral_code': token_rec.sponsor.referral_code,
            'placement_side': token_rec.placement_side,
            'is_locked': True,
            'token': token_rec.token,
            'is_active': token_rec.sponsor.is_active
        }

    # 2. Case-insensitive token lookup
    token_rec_upper = db.query(ReferralToken).filter(
        ReferralToken.token == clean_str.upper(),
        ReferralToken.is_active == True
    ).first()

    if token_rec_upper and token_rec_upper.sponsor:
        return {
            'valid': True,
            'sponsor_name': token_rec_upper.sponsor.full_name,
            'sponsor_code': token_rec_upper.sponsor.user_code,
            'referral_code': token_rec_upper.sponsor.referral_code,
            'placement_side': token_rec_upper.placement_side,
            'is_locked': True,
            'token': token_rec_upper.token,
            'is_active': token_rec_upper.sponsor.is_active
        }

    # 3. Fallback: plain sponsor referral code or user code (direct manual entry)
    user = resolve_sponsor_by_code(db, clean_str.upper())
    if not user:
        user = db.query(User).filter(User.user_code == clean_str.upper()).first()

    if user:
        return {
            'valid': True,
            'sponsor_name': user.full_name,
            'sponsor_code': user.user_code,
            'referral_code': user.referral_code,
            'placement_side': None,
            'is_locked': False,
            'token': None,
            'is_active': user.is_active
        }

    return {'valid': False, 'error': f"Referral '{token_or_code}' is invalid or does not exist."}
