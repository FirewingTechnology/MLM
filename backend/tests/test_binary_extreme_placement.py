import pytest
from app.models.user import User
from app.models.volume_ledger import VolumeLedger
from app.services.mlm_service import (
    find_extreme_placement,
    auto_place_in_binary_tree,
    get_binary_ancestors,
    build_binary_tree_node
)
from app.services.commission_service import process_package_purchase
from app.services.pair_service import pair_service
from app.services.time_service import time_provider

# ====================================================================
# BINARY EXTREME PLACEMENT TEST SUITE
# ====================================================================

def test_1_first_left_placement(client, db_session):
    """1. First LEFT placement under root A is placed at (A, LEFT)."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    res = client.post("/api/auth/register", json={
        "full_name": "Member B",
        "email": "b_left1@demo.com",
        "mobile": "9811000001",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": amol.referral_code,
        "binary_position": "LEFT"
    })
    assert res.status_code == 201
    b = db_session.query(User).filter(User.email == "b_left1@demo.com").first()

    assert b.sponsor_id == amol.id
    assert b.binary_parent_id == amol.id
    assert b.binary_position == "LEFT"


def test_2_repeated_left_placement_follows_extreme_left(client, db_session):
    """
    2. Repeated LEFT placement under A follows extreme-left:
       A -> B (LEFT of A) -> C (LEFT of B) -> D (LEFT of C) -> E (LEFT of D)
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # 1. Register B on LEFT
    client.post("/api/auth/register", json={
        "full_name": "Member B", "email": "b_ext@demo.com", "mobile": "9812000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b_ext@demo.com").first()
    assert b.binary_parent_id == amol.id
    assert b.binary_position == "LEFT"

    # 2. Register C on LEFT under A
    client.post("/api/auth/register", json={
        "full_name": "Member C", "email": "c_ext@demo.com", "mobile": "9812000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    c = db_session.query(User).filter(User.email == "c_ext@demo.com").first()
    assert c.binary_parent_id == b.id
    assert c.binary_position == "LEFT"

    # 3. Register D on LEFT under A
    client.post("/api/auth/register", json={
        "full_name": "Member D", "email": "d_ext@demo.com", "mobile": "9812000003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "d_ext@demo.com").first()
    assert d.binary_parent_id == c.id
    assert d.binary_position == "LEFT"

    # 4. Register E on LEFT under A
    client.post("/api/auth/register", json={
        "full_name": "Member E", "email": "e_ext@demo.com", "mobile": "9812000004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    e = db_session.query(User).filter(User.email == "e_ext@demo.com").first()
    assert e.binary_parent_id == d.id
    assert e.binary_position == "LEFT"


def test_3_first_right_placement(client, db_session):
    """3. First RIGHT placement under root A is placed at (A, RIGHT)."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    res = client.post("/api/auth/register", json={
        "full_name": "Member X",
        "email": "x_right1@demo.com",
        "mobile": "9813000001",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": amol.referral_code,
        "binary_position": "RIGHT"
    })
    assert res.status_code == 201
    x = db_session.query(User).filter(User.email == "x_right1@demo.com").first()

    assert x.sponsor_id == amol.id
    assert x.binary_parent_id == amol.id
    assert x.binary_position == "RIGHT"


def test_4_repeated_right_placement_follows_extreme_right(client, db_session):
    """
    4. Repeated RIGHT placement under A follows extreme-right:
       A -> X (RIGHT of A) -> Y (RIGHT of X) -> Z (RIGHT of Y)
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # 1. Register X on RIGHT
    client.post("/api/auth/register", json={
        "full_name": "Member X", "email": "x_ext@demo.com", "mobile": "9814000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    x = db_session.query(User).filter(User.email == "x_ext@demo.com").first()
    assert x.binary_parent_id == amol.id
    assert x.binary_position == "RIGHT"

    # 2. Register Y on RIGHT under A
    client.post("/api/auth/register", json={
        "full_name": "Member Y", "email": "y_ext@demo.com", "mobile": "9814000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    y = db_session.query(User).filter(User.email == "y_ext@demo.com").first()
    assert y.binary_parent_id == x.id
    assert y.binary_position == "RIGHT"

    # 3. Register Z on RIGHT under A
    client.post("/api/auth/register", json={
        "full_name": "Member Z", "email": "z_ext@demo.com", "mobile": "9814000003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    z = db_session.query(User).filter(User.email == "z_ext@demo.com").first()
    assert z.binary_parent_id == y.id
    assert z.binary_position == "RIGHT"


def test_5_existing_nodes_never_moved(client, db_session):
    """5. Existing nodes are never moved or modified during subsequent registrations."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # Register B and X
    client.post("/api/auth/register", json={
        "full_name": "Node B", "email": "b_stay@demo.com", "mobile": "9815000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    client.post("/api/auth/register", json={
        "full_name": "Node X", "email": "x_stay@demo.com", "mobile": "9815000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    b = db_session.query(User).filter(User.email == "b_stay@demo.com").first()
    x = db_session.query(User).filter(User.email == "x_stay@demo.com").first()

    b_id, b_parent, b_pos = b.id, b.binary_parent_id, b.binary_position
    x_id, x_parent, x_pos = x.id, x.binary_parent_id, x.binary_position

    # Register several more users
    for i in range(3, 8):
        client.post("/api/auth/register", json={
            "full_name": f"Node L{i}", "email": f"l{i}_stay@demo.com", "mobile": f"981500000{i}",
            "password": "Demo@123", "confirm_password": "Demo@123",
            "referral_code": amol.referral_code, "binary_position": "LEFT"
        })

    # Reload B and X from DB
    db_session.expire_all()
    b_reload = db_session.get(User, b_id)
    x_reload = db_session.get(User, x_id)

    assert b_reload.binary_parent_id == b_parent
    assert b_reload.binary_position == b_pos
    assert x_reload.binary_parent_id == x_parent
    assert x_reload.binary_position == x_pos


def test_6_sponsor_independence_from_placement_parent(client, db_session):
    """
    6. Direct Sponsor remains independent from Binary Placement Parent.
       A sponsors B, C, D.
       Binary tree: A -> B -> C -> D.
       All 3 have sponsor_id = A.id.
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    for name, email, mobile in [
        ("SponsorTest B", "sp_b@demo.com", "9816000001"),
        ("SponsorTest C", "sp_c@demo.com", "9816000002"),
        ("SponsorTest D", "sp_d@demo.com", "9816000003"),
    ]:
        client.post("/api/auth/register", json={
            "full_name": name, "email": email, "mobile": mobile,
            "password": "Demo@123", "confirm_password": "Demo@123",
            "referral_code": amol.referral_code, "binary_position": "LEFT"
        })

    b = db_session.query(User).filter(User.email == "sp_b@demo.com").first()
    c = db_session.query(User).filter(User.email == "sp_c@demo.com").first()
    d = db_session.query(User).filter(User.email == "sp_d@demo.com").first()

    # All 3 are directly sponsored by A
    assert b.sponsor_id == amol.id
    assert c.sponsor_id == amol.id
    assert d.sponsor_id == amol.id

    # Binary tree placement is hierarchical extreme-left
    assert b.binary_parent_id == amol.id
    assert c.binary_parent_id == b.id
    assert d.binary_parent_id == c.id


def test_7_left_placement_never_enters_right_branch(client, db_session):
    """7. LEFT placement never enters RIGHT branch even when RIGHT branch is empty."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # 1. Register B on LEFT
    client.post("/api/auth/register", json={
        "full_name": "Branch B", "email": "br_b@demo.com", "mobile": "9817000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    # 2. Register C on LEFT again (A's RIGHT is completely empty)
    client.post("/api/auth/register", json={
        "full_name": "Branch C", "email": "br_c@demo.com", "mobile": "9817000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })

    b = db_session.query(User).filter(User.email == "br_b@demo.com").first()
    c = db_session.query(User).filter(User.email == "br_c@demo.com").first()

    # C must be under B on LEFT, NOT placed in A's empty RIGHT slot
    assert c.binary_parent_id == b.id
    assert c.binary_position == "LEFT"

    # A's RIGHT child must still be None
    a_right = db_session.query(User).filter(User.binary_parent_id == amol.id, User.binary_position == "RIGHT").first()
    assert a_right is None


def test_8_right_placement_never_enters_left_branch(client, db_session):
    """8. RIGHT placement never enters LEFT branch even when LEFT branch is empty."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # 1. Register X on RIGHT
    client.post("/api/auth/register", json={
        "full_name": "Branch X", "email": "br_x@demo.com", "mobile": "9818000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    # 2. Register Y on RIGHT again (A's LEFT is completely empty)
    client.post("/api/auth/register", json={
        "full_name": "Branch Y", "email": "br_y@demo.com", "mobile": "9818000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })

    x = db_session.query(User).filter(User.email == "br_x@demo.com").first()
    y = db_session.query(User).filter(User.email == "br_y@demo.com").first()

    # Y must be under X on RIGHT, NOT placed in A's empty LEFT slot
    assert y.binary_parent_id == x.id
    assert y.binary_position == "RIGHT"

    # A's LEFT child must still be None
    a_left = db_session.query(User).filter(User.binary_parent_id == amol.id, User.binary_position == "LEFT").first()
    assert a_left is None


def test_9_mixed_branch_operations(client, db_session):
    """
    9. Mixed Branch Operations:
       Start: A
       Register: B -> A LEFT, C -> A RIGHT
       Register: D -> A LEFT, E -> A RIGHT
       Expected Tree:
              A
             / \
            B   C
           /     \
          D       E
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # B -> A LEFT
    client.post("/api/auth/register", json={
        "full_name": "Mix B", "email": "mix_b@demo.com", "mobile": "9819000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    # C -> A RIGHT
    client.post("/api/auth/register", json={
        "full_name": "Mix C", "email": "mix_c@demo.com", "mobile": "9819000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })
    # D -> A LEFT (extreme left -> under B)
    client.post("/api/auth/register", json={
        "full_name": "Mix D", "email": "mix_d@demo.com", "mobile": "9819000003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    # E -> A RIGHT (extreme right -> under C)
    client.post("/api/auth/register", json={
        "full_name": "Mix E", "email": "mix_e@demo.com", "mobile": "9819000004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "RIGHT"
    })

    b = db_session.query(User).filter(User.email == "mix_b@demo.com").first()
    c = db_session.query(User).filter(User.email == "mix_c@demo.com").first()
    d = db_session.query(User).filter(User.email == "mix_d@demo.com").first()
    e = db_session.query(User).filter(User.email == "mix_e@demo.com").first()

    assert b.binary_parent_id == amol.id and b.binary_position == "LEFT"
    assert c.binary_parent_id == amol.id and c.binary_position == "RIGHT"
    assert d.binary_parent_id == b.id and d.binary_position == "LEFT"
    assert e.binary_parent_id == c.id and e.binary_position == "RIGHT"


def test_10_deep_ancestors_and_volume_propagation(client, db_session):
    """
    10. Deep extreme-left placement preserves ancestor path and propagates BV correctly.
       A -> B (LEFT) -> C (LEFT) -> D (LEFT)
       D purchases 30,000 BV:
       - C receives 30,000 BV on LEFT
       - B receives 30,000 BV on LEFT
       - A receives 30,000 BV on LEFT
       - Direct Commission (10% = ₹3,000) goes to direct sponsor A
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B, C, D all sponsored by A on LEFT
    client.post("/api/auth/register", json={
        "full_name": "Vol B", "email": "vol_b@demo.com", "mobile": "9820000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    client.post("/api/auth/register", json={
        "full_name": "Vol C", "email": "vol_c@demo.com", "mobile": "9820000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    client.post("/api/auth/register", json={
        "full_name": "Vol D", "email": "vol_d@demo.com", "mobile": "9820000003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })

    b = db_session.query(User).filter(User.email == "vol_b@demo.com").first()
    c = db_session.query(User).filter(User.email == "vol_c@demo.com").first()
    d = db_session.query(User).filter(User.email == "vol_d@demo.com").first()

    ancestors = get_binary_ancestors(db_session, d.id)
    ancestor_ids_and_legs = [(a.id, pos) for a, pos in ancestors]
    assert ancestor_ids_and_legs == [(c.id, "LEFT"), (b.id, "LEFT"), (amol.id, "LEFT")]

    # D purchases package
    process_package_purchase(db_session, d.id)
    db_session.commit()

    c_sum = pair_service.get_user_pair_summary(db_session, c.id, slot_info.slot_id)
    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)

    assert c_sum['effective_left_bv'] == 30000.0
    assert b_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_left_bv'] == 30000.0

    # VolumeLedger entries exist for all 3 ancestors on LEFT
    ledgers = db_session.query(VolumeLedger).filter(VolumeLedger.source_user_id == d.id).all()
    assert len(ledgers) == 3
    assert {l.ancestor_user_id for l in ledgers} == {c.id, b.id, amol.id}
    assert all(l.side == "LEFT" for l in ledgers)


def test_11_build_binary_tree_node_extreme_rendering(client, db_session):
    """11. build_binary_tree_node renders extreme-left structure accurately in the JSON hierarchy."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "Tree B", "email": "tree_b@demo.com", "mobile": "9821000001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })
    client.post("/api/auth/register", json={
        "full_name": "Tree C", "email": "tree_c@demo.com", "mobile": "9821000002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": amol.referral_code, "binary_position": "LEFT"
    })

    b = db_session.query(User).filter(User.email == "tree_b@demo.com").first()
    c = db_session.query(User).filter(User.email == "tree_c@demo.com").first()

    tree = build_binary_tree_node(db_session, amol, depth=3)

    assert tree['id'] == amol.id
    assert tree['left'] is not None
    assert tree['left']['id'] == b.id
    assert tree['left']['left'] is not None
    assert tree['left']['left']['id'] == c.id
    assert tree['right'] is None
