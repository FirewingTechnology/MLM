import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Partner Network Rewards API"
    ENV: str = os.getenv("ENV", "development")
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENV", "development"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "partner-network-rewards-super-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # SQLite Persistent Storage Configuration
    # Local Default: ./data/mlm.sqlite3
    # Production Default (Render Persistent Disk): /var/data/mlm.sqlite3
    SQLITE_DB_PATH: str = os.getenv(
        "SQLITE_DB_PATH",
        os.getenv("DATABASE_URL", "").replace("sqlite:///", "") if os.getenv("DATABASE_URL", "").startswith("sqlite:///") else "./data/mlm.sqlite3"
    )

    # Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.abspath(os.getenv('SQLITE_DB_PATH', './data/mlm.sqlite3'))}"
    )

    # Backups directory
    BACKUP_DIR: str = os.getenv(
        "BACKUP_DIR",
        os.path.join(os.path.dirname(os.path.abspath(os.getenv("SQLITE_DB_PATH", "./data/mlm.sqlite3"))), "backups")
    )

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
    PAIR_BONUS: float = 10000.0                    # Pair Bonus amount per completed pair (₹10,000)
    PAIR_BONUS_AMOUNT: float = 10000.0             # Backward-compatible alias
    MAX_PAIRS_PER_SLOT: int = 1                    # Maximum paid pairs per calculation period/slot (1)
    MAX_PAIRS_PER_PERIOD: int = 1                  # Backward-compatible alias

    # Carry Commission (Override) Configuration
    CARRY_COMMISSION_ENABLED: bool = True          # Enable/disable carry/override commission
    CARRY_COMMISSION_RATE: float = 0.10            # 10% rate
    CARRY_COMMISSION_BASE: str = "PAIR_BONUS"      # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    # Matching / Upline Commission Configuration
    MATCHING_COMMISSION_ENABLED: bool = True       # Enable/disable matching commission on child pairs
    MATCHING_COMMISSION_RATE: float = 0.10          # Configurable matching rate (10% = ₹1,000 on ₹10,000 Pair Bonus)
    MATCHING_COMMISSION_BASE: str = "PAIR_BONUS"   # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    TIMEZONE: str = "Asia/Kolkata"

    # Frontend URL for CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod") or self.ENV.lower() in ("production", "prod")

    @property
    def sanitized_db_path(self) -> str:
        if self.DATABASE_URL.startswith("sqlite"):
            raw_path = self.DATABASE_URL.replace("sqlite:///", "")
            return Path(raw_path).as_posix()
        return "non-sqlite"

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure SQLite database directory & backup directory exist
if settings.DATABASE_URL.startswith("sqlite"):
    db_file = settings.DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(os.path.abspath(db_file))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    if settings.BACKUP_DIR:
        os.makedirs(os.path.abspath(settings.BACKUP_DIR), exist_ok=True)

