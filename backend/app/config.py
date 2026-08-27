import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Virtual Binary MLM API"
    ENV: str = os.getenv("ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "virtual-binary-mlm-super-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database URL - default to SQLite for instant local run, supports PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mlm_demo.db")

    # MLM Business Rules Configuration
    DEFAULT_PACKAGE_PRICE: float = 35000.0
    DEFAULT_PRODUCT_VALUE: float = 30000.0
    DEFAULT_GST_AMOUNT: float = 5000.0
    DEFAULT_PACKAGE_BV: float = 30000.0

    # Commissions & Rates
    DIRECT_COMMISSION_RATE: float = 0.10           # 10% on BV (₹3,000 for 30k BV)
    DIRECT_REFERRAL_COMMISSION_PCT: float = 0.10   # Backward-compatible alias
    BINARY_MATCHING_COMMISSION_PCT: float = 0.10   # 10% on matched BV
    CARRY_FORWARD_ENABLED: bool = True

    # Binary Pair Bonus Engine Configuration
    PAIR_VOLUME: float = 30000.0                   # Qualifying BV threshold per leg (₹30,000)
    PAIR_QUALIFYING_BV: float = 30000.0            # Backward-compatible alias
    PAIR_BONUS: float = 15000.0                    # Pair Bonus amount per completed pair (₹15,000)
    PAIR_BONUS_AMOUNT: float = 15000.0             # Backward-compatible alias
    MAX_PAIRS_PER_SLOT: int = 1                    # Maximum paid pairs per calculation period/slot (1)
    MAX_PAIRS_PER_PERIOD: int = 1                  # Backward-compatible alias

    # Carry Commission (Override) Configuration
    CARRY_COMMISSION_ENABLED: bool = True          # Enable/disable carry/override commission
    CARRY_COMMISSION_RATE: float = 0.10            # 10% rate
    CARRY_COMMISSION_BASE: str = "PAIR_BONUS"      # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    # Matching / Upline Commission Configuration
    MATCHING_COMMISSION_ENABLED: bool = True       # Enable/disable matching commission on child pairs
    MATCHING_COMMISSION_RATE: float = 0.10          # Configurable matching rate (10% = ₹1,500 on ₹15,000 Pair Bonus)
    MATCHING_COMMISSION_BASE: str = "PAIR_BONUS"   # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    TIMEZONE: str = "Asia/Kolkata"

    # Frontend URL for CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        case_sensitive = True

settings = Settings()
