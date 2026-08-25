import uuid
import time
import random

def generate_custom_id(prefix: str) -> str:
    timestamp_part = int(time.time() * 1000) % 1000000
    random_part = random.randint(100, 999)
    return f"{prefix}-{timestamp_part}{random_part}"

def generate_user_code(seq: int = None) -> str:
    if seq is not None:
        return f"USR-{seq:05d}"
    return generate_custom_id("USR")

def generate_referral_code(name: str) -> str:
    clean_name = "".join(filter(str.isalnum, name)).upper()[:4]
    if len(clean_name) < 4:
        clean_name = clean_name.ljust(4, "X")
    rand = random.randint(1000, 9999)
    return f"{clean_name}{rand}"

def generate_purchase_code() -> str:
    return generate_custom_id("PUR")

def generate_commission_code() -> str:
    return generate_custom_id("COM")

def generate_transaction_code() -> str:
    return generate_custom_id("TXN")

def generate_withdrawal_code() -> str:
    return generate_custom_id("WDR")
